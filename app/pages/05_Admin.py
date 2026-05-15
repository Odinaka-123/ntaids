"""
pages/05_Admin.py
─────────────────
Admin-only panel: user management, role assignment, audit log viewer.
Requires admin role + admin_panel permission.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.auth_middleware import require_auth, require_permission, user_badge, audit
from src.auth_db import (
    get_all_users, toggle_user_active, create_user,
    get_audit_log, has_permission,
)

st.set_page_config(
    page_title="NTA-IDS · Admin",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth gate ─────────────────────────────────────────────────
user = require_auth()
require_permission(user, "admin_panel", "can_read")
user_badge(user)

# ── CSS (shared palette) ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; color: #e2e8f0; }
.stApp {
    background: #05070d;
    background-image: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,128,0.05) 0%, transparent 70%);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem !important; max-width: 1300px !important; }
.section-head {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.16em; text-transform: uppercase; color: #4ade80;
    padding: 0 0 0.5rem; border-bottom: 1px solid rgba(0,255,128,0.12);
    margin: 2rem 0 1rem;
}
.stButton > button {
    background: linear-gradient(135deg, #00c46a, #00ff80) !important;
    color: #052e16 !important; font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important; font-size: 0.78rem !important;
    letter-spacing: 0.08em !important; border: none !important;
    border-radius: 8px !important; padding: 0.5rem 1.2rem !important;
    box-shadow: 0 0 16px rgba(0,255,128,0.2) !important;
}
.stTextInput > label, .stSelectbox > label {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.62rem !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important; color: #64748b !important;
}
.stTextInput > div > div > input, .stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.82rem !important;
}
[data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 10px !important; }
.stAlert { border-radius: 8px !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 0.74rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:1rem; padding:1.2rem 0 1rem;
            border-bottom:1px solid rgba(0,255,128,0.15); margin-bottom:1.5rem;">
  <div style="width:40px;height:40px;background:linear-gradient(135deg,#00ff80,#00c46a);
              border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;
              box-shadow:0 0 20px rgba(0,255,128,0.3);">⚙️</div>
  <div>
    <p style="font-family:'IBM Plex Mono',monospace;font-size:1.15rem;font-weight:600;
              letter-spacing:0.08em;color:#f0fdf4;margin:0;">ADMIN PANEL</p>
    <p style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;letter-spacing:0.14em;
              text-transform:uppercase;color:#4ade80;margin:0.2rem 0 0;">
      User Management · Roles · Audit Log</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 01 · USERS
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">01 · USER ACCOUNTS</div>', unsafe_allow_html=True)

users = get_all_users()
if users:
    df_users = pd.DataFrame(users)
    df_users["created_at"] = pd.to_datetime(df_users["created_at"], unit="s").dt.strftime("%Y-%m-%d %H:%M")
    df_users["last_login"]  = pd.to_datetime(df_users["last_login"],  unit="s", errors="coerce").dt.strftime("%Y-%m-%d %H:%M").fillna("Never")
    df_users["active"]      = df_users["is_active"].map({1: "✅", 0: "🚫"})
    show_cols = ["id", "username", "email", "role", "active", "created_at", "last_login"]

    st.dataframe(
        df_users[show_cols],
        use_container_width=True,
        hide_index=True,
        height=280,
        column_config={
            "id":         st.column_config.NumberColumn("ID",       width="small"),
            "username":   st.column_config.TextColumn("Username"),
            "email":      st.column_config.TextColumn("Email"),
            "role":       st.column_config.TextColumn("Role"),
            "active":     st.column_config.TextColumn("Status",    width="small"),
            "created_at": st.column_config.TextColumn("Created"),
            "last_login": st.column_config.TextColumn("Last Login"),
        }
    )

    # Toggle active
    st.markdown('<div class="section-head">02 · TOGGLE USER STATUS</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])
    user_map = {u["username"]: u for u in users}
    with col1:
        target = st.selectbox("Select user", [u["username"] for u in users if str(u["id"]) != str(user.get("user_id", user.get("id", "")))])
    with col2:
        action_lbl = st.selectbox("Action", ["Activate", "Deactivate"])
    with col3:
        st.markdown("<div style='height:1.72rem'></div>", unsafe_allow_html=True)
        if st.button("Apply"):
            uid = user_map[target]["id"]
            toggle_user_active(uid, action_lbl == "Activate")
            audit(user, action_lbl.lower(), "admin_panel", f"target={target}")
            st.success(f"User **{target}** {action_lbl.lower()}d.", icon="✅")
            st.rerun()

# ══════════════════════════════════════════════════════════════
# 03 · CREATE USER (admin only)
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">03 · CREATE USER</div>', unsafe_allow_html=True)

with st.expander("➕  New Account", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        nu = st.text_input("Username",  key="nu")
        ne = st.text_input("Email",     key="ne")
    with c2:
        np_ = st.text_input("Password", type="password", key="np_")
        nr  = st.selectbox("Role",      ["analyst", "viewer", "admin"], key="nr")

    if st.button("Create", key="btn_create_user"):
        if not all([nu, ne, np_]):
            st.error("All fields required.", icon="⚠️")
        else:
            res = create_user(nu, ne, np_, role=nr)
            if res["ok"]:
                audit(user, "create_user", "admin_panel", f"new_user={nu} role={nr}")
                st.success(f"User **{nu}** created with role **{nr}**.", icon="✅")
                st.rerun()
            else:
                st.error(res["error"], icon="🚫")

# ══════════════════════════════════════════════════════════════
# 04 · AUDIT LOG
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="section-head">04 · AUDIT LOG</div>', unsafe_allow_html=True)

if has_permission(user["role"], "audit_log", "can_read"):
    logs = get_audit_log(limit=200)
    if logs:
        df_log = pd.DataFrame(logs)
        df_log["ts"] = pd.to_datetime(df_log["ts"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(
            df_log[["ts", "username", "action", "resource", "detail"]],
            use_container_width=True,
            hide_index=True,
            height=300,
        )
    else:
        st.info("No audit entries yet.", icon="ℹ️")
else:
    st.warning("Audit log access requires elevated permissions.", icon="🔒")

# ── Footer ────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem; padding-top:1rem; border-top:1px solid rgba(255,255,255,0.05);
            font-family:'IBM Plex Mono',monospace; font-size:0.62rem; color:#334155;">
  NTA-IDS Admin Panel · SQLite Auth + Permit DB
</div>
""", unsafe_allow_html=True)