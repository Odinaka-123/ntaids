with open('app/pages/01_Dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
from pathlib import Path
from src.auth_middleware import require_auth, user_badge
user = require_auth()
user_badge(user)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config('''

new = '''import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Page config must be first ──────────────────────────────────────────────────
st.set_page_config('''

content = content.replace(old, new)

# Now add auth after set_page_config closing paren
old2 = '''    initial_sidebar_state="collapsed",
)'''
new2 = '''    initial_sidebar_state="collapsed",
)

from src.auth_middleware import require_auth, user_badge
user = require_auth()
user_badge(user)'''

content = content.replace(old2, new2, 1)

with open('app/pages/01_Dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
