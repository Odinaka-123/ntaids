"""
src/auth_middleware.py
──────────────────────
Drop-in auth guard for any NTA-IDS Streamlit page.

Usage at the top of any protected page:
    from src.auth_middleware import require_auth, require_permission, user_badge
    user = require_auth()
    user_badge(user)
"""

import streamlit as st
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.auth_db import validate_session, has_permission, log_action, revoke_session


def _current_user():
    token = st.session_state.get("auth_token")
    if not token:
        return None
    return validate_session(token)


def require_auth() -> dict:
    """
    Validates session. If invalid/missing, shows a redirect prompt and stops.
    Returns the user dict on success.
    """
    try:
        st.set_page_config(
            page_title="NTA-IDS",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except st.errors.StreamlitAPIException:
        pass  # already set by the calling page

    user = _current_user()
    if user:
        return user

    # Not authed — show lock screen
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');
    .stApp { background:#05070d; }
    #MainMenu, footer, header { visibility:hidden; }
    </style>
    <div style="
        margin: 6rem auto 0; max-width: 400px; text-align: center;
        font-family: 'IBM Plex Mono', monospace;
    ">
      <div style="
          width:56px; height:56px; border-radius:14px;
          background:linear-gradient(135deg,#00ff80,#00c46a);
          display:flex; align-items:center; justify-content:center;
          font-size:1.5rem; margin:0 auto 1.2rem;
          box-shadow:0 0 32px rgba(0,255,128,0.3);
      ">🔐</div>
      <p style="color:#f0fdf4; font-size:1.1rem; font-weight:600; letter-spacing:0.1em; margin:0;">
        ACCESS RESTRICTED
      </p>
      <p style="color:#4ade80; font-size:0.65rem; letter-spacing:0.14em; margin:0.4rem 0 1.6rem;">
        AUTHENTICATION REQUIRED
      </p>
      <p style="color:#475569; font-size:0.72rem; line-height:1.8;">
        You must sign in before accessing NTA-IDS.<br>
        Navigate to <strong style="color:#64748b;">Login</strong> in the sidebar.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


def require_permission(user: dict, resource: str, action: str = "can_read"):
    """
    Checks permit DB. Stops the page with a 403 card if permission denied.
    """
    if not has_permission(user["role"], resource, action):
        st.markdown(f"""
        <div style="
            margin: 4rem auto 0; max-width: 420px;
            background: rgba(239,68,68,0.06);
            border: 1px solid rgba(239,68,68,0.2);
            border-radius: 12px; padding: 2rem;
            font-family: 'IBM Plex Mono', monospace; text-align: center;
        ">
          <p style="color:#f87171; font-size:1rem; font-weight:600; letter-spacing:0.08em; margin:0 0 0.5rem;">
            🚫 PERMISSION DENIED
          </p>
          <p style="color:#64748b; font-size:0.72rem; line-height:1.8; margin:0;">
            Role <strong style="color:#94a3b8;">{user['role'].upper()}</strong>
            does not have <strong style="color:#94a3b8;">{action}</strong>
            access to <strong style="color:#94a3b8;">{resource}</strong>.<br>
            Contact your administrator to request access.
          </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()


def audit(user: dict, action: str, resource: str, detail: str = ""):
    """Thin wrapper to log an action to the permits audit_log."""
    log_action(user["id"], user["username"], action, resource, detail)


def user_badge(user: dict):
    """Renders sidebar nav: user pill, page links, and sign out."""
    role_colors = {
        "admin":   ("#ef4444", "rgba(239,68,68,0.12)"),
        "analyst": ("#4ade80", "rgba(0,255,128,0.10)"),
        "viewer":  ("#94a3b8", "rgba(148,163,184,0.10)"),
    }
    color, bg = role_colors.get(user["role"], ("#94a3b8", "rgba(148,163,184,0.10)"))

    # ── User pill ────────────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style="
        padding: 0.75rem 1rem; margin-bottom: 0.75rem;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        font-family: 'IBM Plex Mono', monospace;
    ">
      <div style="font-size:0.62rem; color:#475569; letter-spacing:0.1em; text-transform:uppercase;">
        Signed in as
      </div>
      <div style="color:#f0fdf4; font-size:0.82rem; font-weight:600; margin:0.2rem 0 0.15rem;">
        {user['username']}
      </div>
      <span style="
          display:inline-block; padding:0.15rem 0.55rem; border-radius:100px;
          background:{bg}; color:{color};
          border:1px solid {color}40;
          font-size:0.6rem; letter-spacing:0.06em;
      ">{user['role'].upper()}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation ───────────────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
                letter-spacing:0.12em; text-transform:uppercase; color:#475569;
                margin-bottom:0.4rem;">
      Navigation
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.page_link("pages/01_Dashboard.py", label="🛡️  Dashboard")

    if user["role"] == "admin":
        st.sidebar.page_link("pages/05_Admin.py", label="⚙️  Admin Panel")

    st.sidebar.markdown("<hr style='border-color:rgba(255,255,255,0.06); margin:0.75rem 0'>", unsafe_allow_html=True)

    # ── Sign out ─────────────────────────────────────────────────────────────
    if st.sidebar.button("🔒  Sign Out", use_container_width=True):
        token = st.session_state.get("auth_token")
        if token:
            revoke_session(token)
        st.session_state.pop("auth_token", None)
        st.switch_page("Login.py")