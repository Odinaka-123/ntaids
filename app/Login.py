"""
app/Login.py
─────────────────
Authentication gate for NTA-IDS.
Entry point: streamlit run app/Login.py
"""

import streamlit as st
import sys
from pathlib import Path

# app/Login.py  →  parent = app/  →  parent.parent = ntaids/ (project root)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Guarantee db/ folder exists BEFORE importing auth_db (which opens the DBs)
(ROOT / "db").mkdir(exist_ok=True)

from src.auth_db import (
    authenticate, create_session, validate_session,
    revoke_session, create_user, bootstrap,
    SESSION_TTL_HOURS,
)

# ── Bootstrap tables + default admin on first run ─────────────────────────────
if "bootstrapped" not in st.session_state:
    bootstrap()
    st.session_state["bootstrapped"] = True

st.set_page_config(
    page_title="NTA-IDS · Auth",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #e2e8f0;
}
.stApp {
    background: #05070d;
    background-image: radial-gradient(ellipse 70% 40% at 50% 0%, rgba(0,255,128,0.07) 0%, transparent 70%);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3rem 1rem 4rem !important; max-width: 480px !important; }

.auth-logo {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #00ff80, #00c46a);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
    margin: 0 auto 1.2rem;
    box-shadow: 0 0 32px rgba(0,255,128,0.3);
}
.auth-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.2rem; font-weight: 600;
    letter-spacing: 0.1em; color: #f0fdf4;
    text-align: center; margin: 0;
}
.auth-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; letter-spacing: 0.14em;
    text-transform: uppercase; color: #4ade80;
    text-align: center; margin: 0.35rem 0 1.8rem;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px; gap: 4px; padding: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important; letter-spacing: 0.08em !important;
    color: #64748b !important; background: transparent !important;
    border-radius: 6px !important; padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,255,128,0.12) !important;
    color: #4ade80 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }

.stTextInput > label, .stSelectbox > label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.65rem !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important; color: #64748b !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(0,255,128,0.4) !important;
    box-shadow: 0 0 0 2px rgba(0,255,128,0.08) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #00c46a, #00ff80) !important;
    color: #052e16 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    letter-spacing: 0.08em !important; border: none !important;
    border-radius: 8px !important; padding: 0.65rem 1.5rem !important;
    width: 100% !important;
    box-shadow: 0 0 20px rgba(0,255,128,0.2) !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
.stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }

.stAlert {
    border-radius: 8px !important; border-left-width: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.76rem !important;
}
.stSpinner > div { border-top-color: #00ff80 !important; }

.role-pill {
    display: inline-block; padding: 0.18rem 0.65rem;
    border-radius: 100px; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.06em; font-weight: 500;
}
.role-admin   { background: rgba(239,68,68,0.12);   color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.role-analyst { background: rgba(0,255,128,0.10);   color: #4ade80; border: 1px solid rgba(0,255,128,0.25); }
.role-viewer  { background: rgba(148,163,184,0.10); color: #94a3b8; border: 1px solid rgba(148,163,184,0.2); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  Session helpers
# ══════════════════════════════════════════════════════════════

def _get_session():
    token = st.session_state.get("auth_token")
    if not token:
        return None
    user = validate_session(token)
    if not user:
        st.session_state.pop("auth_token", None)
        return None
    return user


def _logout():
    token = st.session_state.get("auth_token")
    if token:
        revoke_session(token)
    st.session_state.pop("auth_token", None)
    st.rerun()


# ══════════════════════════════════════════════════════════════
#  Already authenticated → identity banner
# ══════════════════════════════════════════════════════════════

user = _get_session()

if user:
    role_cls = f"role-{user['role']}"
    st.markdown(f"""
    <div class="auth-logo">🛡️</div>
    <p class="auth-title">NTA-IDS</p>
    <p class="auth-sub">Session Active</p>
    <div style="
        background: rgba(0,255,128,0.04);
        border: 1px solid rgba(0,255,128,0.15);
        border-radius: 12px; padding: 1.4rem 1.6rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem; line-height: 2; color: #94a3b8;
    ">
        <span style="color:#4ade80;">●</span> Authenticated as
        <span style="color:#f0fdf4; font-weight:600;">{user['username']}</span>
        <span class="role-pill {role_cls}" style="margin-left:0.4rem;">{user['role'].upper()}</span><br>
        <span style="color:#4ade80;">›</span> {user['email']}<br>
        <span style="color:#4ade80;">›</span> Session expires in {SESSION_TTL_HOURS}h
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
    st.info("Navigate to **NTA-IDS** from the sidebar to begin analysis.", icon="🔗")
    if st.button("🔒  Sign Out"):
        _logout()
    st.stop()


# ══════════════════════════════════════════════════════════════
#  Auth card
# ══════════════════════════════════════════════════════════════

st.markdown("""
<div class="auth-logo">🛡️</div>
<p class="auth-title">NTA-IDS</p>
<p class="auth-sub">Network Traffic Analyser · Secure Access</p>
""", unsafe_allow_html=True)

tab_login, tab_register = st.tabs(["SIGN IN", "REGISTER"])


# ── Login tab ─────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    username = st.text_input("Username", key="login_user", placeholder="your_username")
    password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    if st.button("⚡  Sign In", key="btn_login"):
        if not username or not password:
            st.error("Please enter both username and password.", icon="⚠️")
        else:
            with st.spinner("Authenticating…"):
                result = authenticate(username.strip(), password)
            if result["ok"]:
                token = create_session(result["user"]["id"])
                st.session_state["auth_token"] = token
                st.success("Authenticated. Redirecting…", icon="✅")
                st.rerun()
            else:
                st.error(result["error"], icon="🚫")

    st.markdown("""
    <div style="margin-top:1.2rem; font-family:'IBM Plex Mono',monospace;
                font-size:0.67rem; color:#334155; line-height:1.9;">
      <span style="color:#4ade80;">›</span> Default admin: <code style="color:#64748b;">admin / Admin@12345</code><br>
      <span style="color:#4ade80;">›</span> Change on first login via the admin panel<br>
      <span style="color:#4ade80;">›</span> 5 failed attempts triggers a 15-min lockout
    </div>
    """, unsafe_allow_html=True)


# ── Register tab ──────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    reg_user  = st.text_input("Username",         key="reg_user",  placeholder="new_analyst")
    reg_email = st.text_input("Email",             key="reg_email", placeholder="you@example.com")
    reg_pw    = st.text_input("Password",          type="password", key="reg_pw",  placeholder="8+ characters")
    reg_pw2   = st.text_input("Confirm Password",  type="password", key="reg_pw2", placeholder="repeat password")
    reg_role  = st.selectbox("Role", ["analyst", "viewer"], key="reg_role",
                              help="Admin accounts must be created by an existing admin.")
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    if st.button("📋  Create Account", key="btn_register"):
        errs = []
        if not all([reg_user, reg_email, reg_pw, reg_pw2]):
            errs.append("All fields are required.")
        if reg_pw != reg_pw2:
            errs.append("Passwords do not match.")
        if len(reg_pw) < 8:
            errs.append("Password must be at least 8 characters.")
        if "@" not in reg_email:
            errs.append("Enter a valid email address.")

        if errs:
            for e in errs:
                st.error(e, icon="⚠️")
        else:
            with st.spinner("Creating account…"):
                result = create_user(
                    reg_user.strip(),
                    reg_email.strip(),
                    reg_pw,
                    role=reg_role,
                )
            if result["ok"]:
                st.success("Account created! Sign in with your credentials.", icon="✅")
            else:
                st.error(result["error"], icon="🚫")

    st.markdown("""
    <div style="margin-top:1.2rem; font-family:'IBM Plex Mono',monospace;
                font-size:0.67rem; color:#334155; line-height:1.9;">
      <span style="color:#4ade80;">›</span> Analysts: upload, run detection, export<br>
      <span style="color:#4ade80;">›</span> Viewers: read-only dashboard access<br>
      <span style="color:#4ade80;">›</span> Admin roles require existing admin approval
    </div>
    """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem; font-family:'IBM Plex Mono',monospace;
            font-size:0.6rem; color:#1e293b; text-align:center; letter-spacing:0.06em;">
  NTA-IDS · PBKDF2-SHA256 · SQLite Auth + Permit DB
</div>
""", unsafe_allow_html=True)