import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Page config — MUST be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="NTA-IDS · Intrusion Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth ──────────────────────────────────────────────────────────────────────
from src.auth_middleware import require_auth, user_badge
user = require_auth()
user_badge(user)

# ── Global CSS ────────────────────────────────────────────────────────────────
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
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,255,128,0.06) 0%, transparent 70%),
        linear-gradient(180deg, #05070d 0%, #080c14 100%);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 1rem 1rem 3rem !important;
    max-width: 1400px !important;
}
@media (min-width: 640px)  { .block-container { padding: 2rem 2rem 4rem !important; } }
@media (min-width: 1024px) { .block-container { padding: 2rem 3rem 4rem !important; } }

.ids-header {
    display: flex; flex-wrap: wrap; align-items: center; gap: 1rem;
    padding: 1.5rem 0 1.2rem;
    border-bottom: 1px solid rgba(0,255,128,0.15);
    margin-bottom: 1.5rem;
}
.ids-logo {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #00ff80 0%, #00c46a 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.25rem;
    box-shadow: 0 0 24px rgba(0,255,128,0.35);
    flex-shrink: 0;
}
.ids-title-block { flex: 1; min-width: 0; }
.ids-title-block h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: clamp(1.1rem, 4vw, 1.55rem);
    font-weight: 600; letter-spacing: 0.06em; color: #f0fdf4;
    margin: 0; line-height: 1; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.ids-title-block p {
    font-size: clamp(0.6rem, 2vw, 0.78rem); color: #4ade80;
    margin: 0.3rem 0 0; font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.1em; text-transform: uppercase;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.status-bar {
    display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; width: 100%;
}
@media (min-width: 520px) { .status-bar { width: auto; margin-left: auto; } }
.pill {
    padding: 0.28rem 0.75rem; border-radius: 100px;
    font-weight: 500; letter-spacing: 0.05em; white-space: nowrap; font-size: 0.68rem;
}
.pill-ok   { background: rgba(0,255,128,0.12); color: #4ade80; border: 1px solid rgba(0,255,128,0.3); }
.pill-warn { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }

.metric-card {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 1.1rem 1.2rem;
    position: relative; overflow: hidden; transition: border-color 0.2s; margin-bottom: 0;
}
@media (min-width: 640px) { .metric-card { padding: 1.4rem 1.6rem; } }
.metric-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.metric-card.neutral::before { background: linear-gradient(90deg, #334155, #475569); }
.metric-card.safe::before    { background: linear-gradient(90deg, #00ff80, #4ade80); }
.metric-card.danger::before  { background: linear-gradient(90deg, #ef4444, #f97316); }
.metric-card:hover { border-color: rgba(255,255,255,0.14); }
.metric-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: #64748b; margin-bottom: 0.45rem;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: clamp(1.4rem, 5vw, 2rem); font-weight: 600; line-height: 1; color: #f0fdf4;
}
.metric-sub { font-size: 0.72rem; color: #94a3b8; margin-top: 0.3rem; }
.metric-card.danger .metric-value { color: #f87171; }
.metric-card.safe  .metric-value  { color: #4ade80; }

.section-head {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.16em; text-transform: uppercase; color: #4ade80;
    padding: 0 0 0.5rem; border-bottom: 1px solid rgba(0,255,128,0.12); margin: 2rem 0 1rem;
}
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important; overflow: hidden; max-width: 100% !important;
}
[data-testid="stVegaLiteChart"] { border-radius: 10px; overflow: hidden; }
.stButton > button {
    background: linear-gradient(135deg, #00c46a, #00ff80) !important;
    color: #052e16 !important; font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    letter-spacing: 0.08em !important; border: none !important;
    border-radius: 8px !important; padding: 0.65rem 1.5rem !important;
    width: 100% !important; transition: opacity 0.15s, transform 0.1s !important;
    box-shadow: 0 0 20px rgba(0,255,128,0.25) !important;
}
@media (min-width: 640px) { .stButton > button { width: auto !important; } }
.stButton > button:hover  { opacity: 0.9 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }
.stDownloadButton > button {
    background: rgba(255,255,255,0.05) !important; color: #94a3b8 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
    border-radius: 8px !important; width: 100% !important;
}
.stDownloadButton > button:hover { background: rgba(255,255,255,0.09) !important; color: #e2e8f0 !important; }
.stAlert {
    border-radius: 10px !important; border-left-width: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
}
.stSpinner > div { border-top-color: #00ff80 !important; }
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 0.75rem;
}
hr { border-color: rgba(255,255,255,0.06) !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 9px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }
.ids-footer {
    margin-top: 3rem; padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.05);
    font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; color: #334155;
    display: flex; flex-direction: column; gap: 0.25rem;
}
@media (min-width: 640px) {
    .ids-footer { flex-direction: row; justify-content: space-between; align-items: center; }
}
</style>
""", unsafe_allow_html=True)

# ── Load models ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_models():
    try:
        from src.features import engineer_features
        from src.models.lstm import reshape_for_lstm
        from tensorflow import keras
        models = {
            'rf':     joblib.load(ROOT / 'models/rf2_model.pkl'),
            'svm':    joblib.load(ROOT / 'models/svm2_model.pkl'),
            'lstm':   keras.models.load_model(str(ROOT / 'models/lstm2_model')),
            'scaler': joblib.load(ROOT / 'models/scaler2.pkl'),
            'pca':    joblib.load(ROOT / 'models/pca2.pkl'),
            'le':     joblib.load(ROOT / 'models/label_encoder2.pkl'),
        }
        return models, None
    except Exception as e:
        return None, str(e)

models, error = load_models()

# ── Header ────────────────────────────────────────────────────────────────────
model_status_pill = (
    '<span class="pill pill-ok">● MODELS LOADED</span>'
    if not error
    else '<span class="pill pill-warn">⚠ MODELS OFFLINE</span>'
)
n_classes = len(models['le'].classes_) if models else "—"

st.markdown(f"""
<div class="ids-header">
  <div class="ids-logo">🛡️</div>
  <div class="ids-title-block">
    <h1>NTA-IDS</h1>
    <p>Network Traffic Analyser · Intrusion Detection System</p>
  </div>
  <div class="status-bar">
    {model_status_pill}
    <span class="pill pill-ok" style="opacity:.65">{n_classes} CLASSES</span>
  </div>
</div>
""", unsafe_allow_html=True)

if error:
    st.warning(f"**Models unavailable** — {error}  \nRun the training pipeline notebook to generate model artefacts.", icon="⚠️")

# ── Upload ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">01 · DATA INGESTION</div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Upload a **CSV** of network flow records (CICIDS-style features)",
    type=["csv"],
    help="Accepts any CSV with numeric network flow features. Column names are normalised automatically.",
)

if not uploaded:
    st.markdown("""
    <div style="margin-top:1rem; padding:1.2rem 1.6rem; background:rgba(255,255,255,0.02);
                border-radius:10px; border:1px solid rgba(255,255,255,0.06);
                font-family:'IBM Plex Mono',monospace; font-size:0.75rem; color:#475569;">
      <span style="color:#4ade80;">›</span> Awaiting input — upload a CSV to begin analysis<br>
      <span style="color:#4ade80;">›</span> Expected schema: CICIDS2017 / CICIDS2018 network flow features<br>
      <span style="color:#4ade80;">›</span> Ensemble: Random Forest (30%) + SVM (20%) + LSTM (50%)
    </div>
    """, unsafe_allow_html=True)

# ── Analysis ──────────────────────────────────────────────────────────────────
if uploaded:
    df = pd.read_csv(uploaded, low_memory=False)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    st.markdown('<div class="section-head">02 · DATASET PREVIEW</div>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    col_a.markdown(f"""
    <div class="metric-card neutral">
      <div class="metric-label">Total Rows</div>
      <div class="metric-value">{len(df):,}</div>
      <div class="metric-sub">flow records ingested</div>
    </div>""", unsafe_allow_html=True)
    col_b.markdown(f"""
    <div class="metric-card neutral">
      <div class="metric-label">Columns</div>
      <div class="metric-value">{df.shape[1]}</div>
      <div class="metric-sub">feature dimensions</div>
    </div>""", unsafe_allow_html=True)
    numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
    col_c.markdown(f"""
    <div class="metric-card neutral">
      <div class="metric-label">Numeric Features</div>
      <div class="metric-value">{numeric_cols}</div>
      <div class="metric-sub">available for inference</div>
    </div>""", unsafe_allow_html=True)

    st.dataframe(df.head(8), use_container_width=True, height=240)

    st.markdown('<div class="section-head">03 · DETECTION ENGINE</div>', unsafe_allow_html=True)

    if not models:
        st.error("Cannot run detection — models not loaded.", icon="🚫")
    else:
        run = st.button("⚡  Run Intrusion Detection")

        if run:
            from src.features import engineer_features
            from src.models.lstm import reshape_for_lstm

            with st.spinner("Analysing traffic patterns…"):
                X = df.select_dtypes(include=[np.number])
                X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

                train_cols = (
                    list(models['scaler'].feature_names_in_)
                    if hasattr(models['scaler'], 'feature_names_in_')
                    else list(X.columns)
                )
                for col in set(train_cols) - set(X.columns):
                    X[col] = 0
                X = X[train_cols]

                X_scaled   = models['scaler'].transform(X)
                X_pca      = models['pca'].transform(X_scaled)
                rf_proba   = models['rf'].predict_proba(X_pca)
                svm_proba  = models['svm'].predict_proba(X_pca)
                lstm_proba = models['lstm'].predict(reshape_for_lstm(X_pca))

                avg    = (0.3 * rf_proba) + (0.2 * svm_proba) + (0.5 * lstm_proba)
                preds  = np.argmax(avg, axis=1)
                labels = models['le'].inverse_transform(preds)
                confs  = avg.max(axis=1)

            st.markdown('<div class="section-head">04 · THREAT SUMMARY</div>', unsafe_allow_html=True)

            total   = len(labels)
            benign  = int((labels == 'BENIGN').sum())
            attacks = total - benign
            pct     = attacks / total * 100 if total else 0

            r1, r2, r3 = st.columns(3)
            r1.markdown(f"""
            <div class="metric-card neutral">
              <div class="metric-label">Flows Analysed</div>
              <div class="metric-value">{total:,}</div>
              <div class="metric-sub">total records processed</div>
            </div>""", unsafe_allow_html=True)
            r2.markdown(f"""
            <div class="metric-card safe">
              <div class="metric-label">Benign</div>
              <div class="metric-value">{benign:,}</div>
              <div class="metric-sub">{100-pct:.1f}% of traffic</div>
            </div>""", unsafe_allow_html=True)
            r3.markdown(f"""
            <div class="metric-card danger">
              <div class="metric-label">Threats Detected</div>
              <div class="metric-value">{attacks:,}</div>
              <div class="metric-sub">{pct:.1f}% attack rate</div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-head">05 · ATTACK TYPE BREAKDOWN</div>', unsafe_allow_html=True)

            counts = pd.Series(labels).value_counts().reset_index()
            counts.columns = ['Attack Type', 'Count']
            counts['% Share'] = (counts['Count'] / total * 100).round(2)

            col_chart, col_table = st.columns([1, 1], gap="medium")

            with col_chart:
                chart_df = counts.set_index('Attack Type')['Count']
                st.bar_chart(chart_df, color="#00ff80", use_container_width=True, height=260)

            with col_table:
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                def style_row(row):
                    if row['Attack Type'] == 'BENIGN':
                        return ['color:#4ade80'] * len(row)
                    return ['color:#f87171'] * len(row)
                styled = counts.style.apply(style_row, axis=1).format({'Count': '{:,}', '% Share': '{:.2f}%'})
                st.dataframe(styled, use_container_width=True, hide_index=True, height=260)

            st.markdown('<div class="section-head">06 · FLOW-LEVEL PREDICTIONS</div>', unsafe_allow_html=True)

            df_out = df.copy()
            df_out['prediction'] = labels
            df_out['confidence'] = (confs * 100).round(1)
            df_out['threat']     = np.where(labels == 'BENIGN', '✅ Benign', '🚨 Attack')

            preview_cols = ['threat', 'prediction', 'confidence'] + list(
                df.select_dtypes(include=[np.number]).columns[:5]
            )
            st.dataframe(
                df_out[preview_cols].head(200),
                use_container_width=True,
                height=320,
                column_config={
                    'threat':     st.column_config.TextColumn("Status"),
                    'prediction': st.column_config.TextColumn("Predicted Class"),
                    'confidence': st.column_config.ProgressColumn(
                        "Confidence (%)", min_value=0, max_value=100, format="%.1f%%"
                    ),
                }
            )

            st.markdown('<div class="section-head">07 · EXPORT</div>', unsafe_allow_html=True)
            csv_bytes = df_out.to_csv(index=False).encode()
            st.download_button(
                "⬇  Download Full Results (CSV)",
                data=csv_bytes,
                file_name="nta_ids_results.csv",
                mime="text/csv",
            )
            st.markdown(f"""
            <div style="margin-top:0.5rem; font-family:'IBM Plex Mono',monospace;
                        font-size:0.7rem; color:#475569; line-height:1.9;">
              nta_ids_results.csv · {len(df_out):,} rows · {df_out.shape[1]} columns<br>
              includes: raw features + prediction + confidence score + threat flag
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ids-footer">
  <span>NTA-IDS · Ensemble: RF + SVM + LSTM</span>
  <span>© Network Traffic Analyser — Intrusion Detection System</span>
</div>
""", unsafe_allow_html=True)