# NTA-IDS: Network Traffic Analysis for Intrusion Detection

A hybrid machine learning-based Intrusion Detection System that analyzes network traffic flows to detect intrusions in real time.

**Final year project — Computer Science, 400L**

## Overview

This system combines Random Forest, SVM, and LSTM models in an ensemble to detect:
- DDoS attacks
- Port scanning
- Malware transfers
- Zero-day exploits

It uses flow-based analysis (NetFlow/IPFIX) without deep packet inspection, preserving user privacy.

## Architecture
Raw Traffic (NetFlow/IPFIX)
↓
Feature Extraction (statistical + behavioural)
↓
Dimensionality Reduction (PCA + Autoencoder)
↓
Ensemble Classifier (RF + SVM + LSTM)
↓
Intrusion Alert / Benign
## Datasets

- [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) — Canadian Institute for Cybersecurity
- [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset) — University of New South Wales

Download the CSVs and place them in `data/raw/cicids2017/` and `data/raw/unsw/` respectively.

## Setup

```bash
# Requires Python 3.11
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
source venv/Scripts/activate # Git Bash

pip install -r requirements.txt
```

## Usage

Open and run `notebooks/01_main_pipeline.ipynb` cell by cell after placing datasets in `data/raw/`.

## Project Structure
ntaids/
├── data/              # Datasets (not tracked by git)
├── notebooks/         # Main pipeline notebook
├── src/
│   ├── preprocess.py  # Data loading, cleaning, SMOTE
│   ├── features.py    # Feature selection and engineering
│   ├── dimensionality.py  # PCA and autoencoder
│   ├── ensemble.py    # Voting ensemble
│   ├── evaluate.py    # Metrics and plots
│   └── models/
│       ├── random_forest.py
│       ├── svm.py
│       └── lstm.py
├── results/           # Saved models and plots
└── app/               # Streamlit dashboard
## Models

| Model | Role |
|---|---|
| Random Forest | High accuracy, feature importance |
| SVM | Strong on high-dimensional data |
| LSTM | Temporal/sequential pattern detection |
| Ensemble | Combined weighted voting |

## Metrics

Evaluated on accuracy, F1-score, precision, recall, and false-positive rate.

# NTA-IDS Auth Layer

Two SQLite databases, PBKDF2-SHA256 password hashing, session tokens,
role-based permits, and a full admin panel — styled to match NTA-IDS exactly.

---

## Files

```
auth/
├── src/
│   ├── auth_db.py          # Core: users, sessions, permits, audit
│   └── auth_middleware.py  # Page guards: require_auth(), require_permission()
└── pages/
    ├── 00_Login.py         # Login / Register UI (renders first)
    └── 05_Admin.py         # Admin panel: users, roles, audit log
```

---

## Databases

| Database | Location | Tables |
|---|---|---|
| `auth.db` | `db/auth.db` | `users`, `sessions`, `login_attempts` |
| `permits.db` | `db/permits.db` | `roles`, `permissions`, `audit_log` |

Both are auto-created on first run. No migrations needed.

---

## Roles & Permissions

| Resource | Admin | Analyst | Viewer |
|---|---|---|---|
| upload | R W D X | R W X | R |
| detection | R W D X | R W X | R |
| export | R W D X | R X | — |
| admin_panel | R W D X | — | — |
| audit_log | R W D X | R | — |

`R` = read · `W` = write · `D` = delete · `X` = export

---

## Default Admin

```
username: admin
password: Admin@12345
```

**Change this immediately** after first login via the Admin panel.

---

## Integration: Protecting the Main App

Add these two lines at the top of your main `app.py` (after imports):

```python
from src.auth_middleware import require_auth, require_permission, user_badge, audit

user = require_auth()                              # blocks if not signed in
require_permission(user, "detection", "can_read") # blocks if wrong role
user_badge(user)                                   # sidebar identity pill
```

Then wrap export around a permission check:
```python
if has_permission(user["role"], "export", "can_export"):
    st.download_button(...)
    audit(user, "export", "detection", f"{len(df_out)} rows")
```

---

## Security Notes

- Passwords: PBKDF2-HMAC-SHA256, 390,000 iterations, 32-byte random salt per user
- Sessions: 256-bit random URL-safe tokens, 8-hour TTL, stored server-side
- Brute force: 5 failed attempts → 15-minute lockout (per username)
- Tokens stored in `st.session_state` (cleared on tab close)
- Audit log records every privileged action with timestamp + user

---

## Deployment Checklist

- [ ] Change default admin password
- [ ] Move `DB_DIR` to a persistent volume (not inside the app container)
- [ ] Serve over HTTPS only
- [ ] Set `SESSION_TTL_HOURS` to suit your security policy
- [ ] Review `MAX_FAILED_ATTEMPTS` and `LOCKOUT_MINUTES`