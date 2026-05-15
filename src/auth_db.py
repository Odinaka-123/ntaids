"""
auth_db.py
──────────
Two-database auth layer for NTA-IDS:
  • auth.db    — users, sessions, login attempts
  • permits.db — role-based permissions per route/feature
"""

import sqlite3
import hashlib
import hmac
import secrets
import time
from pathlib import Path

# src/auth_db.py → parent = src/ → parent.parent = ntaids/
ROOT   = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "db"
DB_DIR.mkdir(exist_ok=True)

AUTH_DB    = DB_DIR / "auth.db"
PERMITS_DB = DB_DIR / "permits.db"

SESSION_TTL_HOURS   = 8
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES     = 15


# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(32)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 390_000)
    return dk.hex(), salt


def _verify_password(password: str, hashed: str, salt: str) -> bool:
    expected, _ = _hash_password(password, salt)
    return hmac.compare_digest(expected, hashed)


def _now_ts() -> float:
    return time.time()


def _conn(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA foreign_keys=ON")
    return con


# ══════════════════════════════════════════════════════════════
#  Schema bootstrap
# ══════════════════════════════════════════════════════════════

def init_auth_db():
    con = _conn(AUTH_DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'analyst',
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    REAL    NOT NULL,
            last_login    REAL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token        TEXT    PRIMARY KEY,
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at   REAL    NOT NULL,
            expires_at   REAL    NOT NULL,
            ip_address   TEXT,
            user_agent   TEXT
        );
        CREATE TABLE IF NOT EXISTS login_attempts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    NOT NULL COLLATE NOCASE,
            attempted_at REAL    NOT NULL,
            success      INTEGER NOT NULL DEFAULT 0,
            ip_address   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_user ON login_attempts(username, attempted_at);
    """)
    con.commit()
    con.close()


def init_permits_db():
    con = _conn(PERMITS_DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS roles (
            name        TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            created_at  REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS permissions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            role       TEXT    NOT NULL REFERENCES roles(name) ON DELETE CASCADE,
            resource   TEXT    NOT NULL,
            can_read   INTEGER NOT NULL DEFAULT 0,
            can_write  INTEGER NOT NULL DEFAULT 0,
            can_delete INTEGER NOT NULL DEFAULT 0,
            can_export INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL,
            username TEXT    NOT NULL,
            action   TEXT    NOT NULL,
            resource TEXT    NOT NULL,
            detail   TEXT,
            ts       REAL    NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_role_resource ON permissions(role, resource);
        CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, ts);
    """)
    con.commit()

    ts = _now_ts()
    for name, desc in [
        ("admin",   "Full system access"),
        ("analyst", "Upload and analyse traffic"),
        ("viewer",  "Read-only dashboard access"),
    ]:
        con.execute("INSERT OR IGNORE INTO roles VALUES (?, ?, ?)", (name, desc, ts))

    perms = {
        "admin":   {"upload": (1,1,1,1), "detection": (1,1,1,1), "export": (1,1,1,1), "admin_panel": (1,1,1,1), "audit_log": (1,1,1,1)},
        "analyst": {"upload": (1,1,0,1), "detection": (1,1,0,1), "export": (1,0,0,1), "admin_panel": (0,0,0,0), "audit_log": (1,0,0,0)},
        "viewer":  {"upload": (1,0,0,0), "detection": (1,0,0,0), "export": (0,0,0,0), "admin_panel": (0,0,0,0), "audit_log": (0,0,0,0)},
    }
    for role, rmap in perms.items():
        for res, (r, w, d, e) in rmap.items():
            con.execute(
                "INSERT OR IGNORE INTO permissions (role, resource, can_read, can_write, can_delete, can_export) VALUES (?,?,?,?,?,?)",
                (role, res, r, w, d, e),
            )
    con.commit()
    con.close()


# ══════════════════════════════════════════════════════════════
#  User management
# ══════════════════════════════════════════════════════════════

def create_user(username: str, email: str, password: str, role: str = "analyst") -> dict:
    if len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters."}
    if role not in ("admin", "analyst", "viewer"):
        return {"ok": False, "error": "Invalid role."}

    pw_hash, salt = _hash_password(password)
    try:
        con = _conn(AUTH_DB)
        con.execute(
            "INSERT INTO users (username, email, password_hash, salt, role, created_at) VALUES (?,?,?,?,?,?)",
            (username.strip(), email.strip().lower(), pw_hash, salt, role, _now_ts()),
        )
        con.commit()
        con.close()
        return {"ok": True}
    except sqlite3.IntegrityError as e:
        msg = "Username already taken." if "username" in str(e) else "Email already registered."
        return {"ok": False, "error": msg}


def _is_locked_out(username: str) -> bool:
    con = _conn(AUTH_DB)
    cutoff = _now_ts() - LOCKOUT_MINUTES * 60
    row = con.execute(
        "SELECT COUNT(*) AS n FROM login_attempts WHERE username=? AND attempted_at>? AND success=0",
        (username, cutoff),
    ).fetchone()
    con.close()
    return row["n"] >= MAX_FAILED_ATTEMPTS


def authenticate(username: str, password: str) -> dict:
    if _is_locked_out(username):
        return {"ok": False, "error": f"Account locked for {LOCKOUT_MINUTES} min after repeated failures."}

    con = _conn(AUTH_DB)
    try:
        user = con.execute(
            "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
        ).fetchone()

        success = user is not None and _verify_password(password, user["password_hash"], user["salt"])

        con.execute(
            "INSERT INTO login_attempts (username, attempted_at, success) VALUES (?,?,?)",
            (username, _now_ts(), int(success)),
        )
        if success:
            con.execute("UPDATE users SET last_login=? WHERE id=?", (_now_ts(), user["id"]))
        con.commit()
    finally:
        con.close()

    if not success:
        return {"ok": False, "error": "Invalid credentials."}
    return {"ok": True, "user": dict(user)}


# ══════════════════════════════════════════════════════════════
#  Session management
# ══════════════════════════════════════════════════════════════

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    now   = _now_ts()
    exp   = now + SESSION_TTL_HOURS * 3600
    con   = _conn(AUTH_DB)
    con.execute(
        "INSERT INTO sessions VALUES (?,?,?,?,?,?)",
        (token, user_id, now, exp, None, None),
    )
    con.commit()
    con.close()
    return token


def validate_session(token: str):
    if not token:
        return None
    con = _conn(AUTH_DB)
    row = con.execute(
        """SELECT s.*, u.username, u.email, u.role
           FROM sessions s JOIN users u ON u.id = s.user_id
           WHERE s.token=? AND s.expires_at>?""",
        (token, _now_ts()),
    ).fetchone()
    con.close()
    return dict(row) if row else None


def revoke_session(token: str):
    con = _conn(AUTH_DB)
    con.execute("DELETE FROM sessions WHERE token=?", (token,))
    con.commit()
    con.close()


# ══════════════════════════════════════════════════════════════
#  Permit checks
# ══════════════════════════════════════════════════════════════

def has_permission(role: str, resource: str, action: str = "can_read") -> bool:
    if action not in {"can_read", "can_write", "can_delete", "can_export"}:
        return False
    con = _conn(PERMITS_DB)
    row = con.execute(
        f"SELECT {action} FROM permissions WHERE role=? AND resource=?", (role, resource)
    ).fetchone()
    con.close()
    return bool(row and row[action])


def log_action(user_id: int, username: str, action: str, resource: str, detail: str = ""):
    con = _conn(PERMITS_DB)
    con.execute(
        "INSERT INTO audit_log (user_id, username, action, resource, detail, ts) VALUES (?,?,?,?,?,?)",
        (user_id, username, action, resource, detail, _now_ts()),
    )
    con.commit()
    con.close()


def get_audit_log(limit: int = 100):
    con = _conn(PERMITS_DB)
    rows = con.execute("SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_all_users():
    con = _conn(AUTH_DB)
    rows = con.execute(
        "SELECT id, username, email, role, is_active, created_at, last_login FROM users ORDER BY created_at DESC"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id: int, active: bool):
    con = _conn(AUTH_DB)
    con.execute("UPDATE users SET is_active=? WHERE id=?", (int(active), user_id))
    con.commit()
    con.close()


# ══════════════════════════════════════════════════════════════
#  Bootstrap — call explicitly AFTER db/ folder is guaranteed
# ══════════════════════════════════════════════════════════════

def bootstrap(admin_password: str = "Admin@12345"):
    """
    Creates all tables and seeds default admin + roles.
    Completely safe to call repeatedly — uses IF NOT EXISTS + INSERT OR IGNORE.
    """
    init_auth_db()
    init_permits_db()
    return create_user("admin", "admin@nta-ids.local", admin_password, role="admin")


if __name__ == "__main__":
    print(bootstrap())