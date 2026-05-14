import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.features import engineer_features
from src.models.lstm import reshape_for_lstm
from tensorflow import keras

st.set_page_config(page_title="NTA-IDS Dashboard", layout="wide")
st.title("NTA-IDS — Network Intrusion Detection System")
st.markdown("Upload a CSV of network flow records to detect intrusions.")

@st.cache_resource
def load_models():
    models = {}
    try:
        models['rf']     = joblib.load(ROOT / 'models/rf2_model.pkl')
        models['svm']    = joblib.load(ROOT / 'models/svm2_model.pkl')
        models['lstm']   = keras.models.load_model(str(ROOT / 'models/lstm2_model'))
        models['scaler'] = joblib.load(ROOT / 'models/scaler2.pkl')
        models['pca']    = joblib.load(ROOT / 'models/pca2.pkl')
        models['le']     = joblib.load(ROOT / 'models/label_encoder2.pkl')
        return models, None
    except Exception as e:
        return None, str(e)

models, error = load_models()
if error:
    st.warning(f"Models not loaded yet: {error}")
    st.info("Train the models first by running the main pipeline notebook.")
else:
    st.success(f"All models loaded — {len(models['le'].classes_)} attack classes.")

st.divider()
uploaded = st.file_uploader("Upload network flow CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded, low_memory=False)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    st.write(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
    st.dataframe(df.head())

    if models and st.button("Run Detection"):
        with st.spinner("Analysing traffic..."):
            X = df.select_dtypes(include=[np.number])
            X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
            train_cols = list(models['scaler'].feature_names_in_) if hasattr(models['scaler'], 'feature_names_in_') else list(X.columns)
            for col in set(train_cols) - set(X.columns):
                X[col] = 0
            X = X[train_cols]
            X_scaled = models['scaler'].transform(X)
            X_pca    = models['pca'].transform(X_scaled)
            rf_proba   = models['rf'].predict_proba(X_pca)
            svm_proba  = models['svm'].predict_proba(X_pca)
            lstm_proba = models['lstm'].predict(reshape_for_lstm(X_pca))
            avg    = (0.3 * rf_proba) + (0.2 * svm_proba) + (0.5 * lstm_proba)
            preds  = np.argmax(avg, axis=1)
            labels = models['le'].inverse_transform(preds)

        st.divider()
        st.subheader("Detection Results")
        total   = len(labels)
        benign  = (labels == 'BENIGN').sum()
        attacks = total - benign
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Flows",      f"{total:,}")
        col2.metric("Benign",           f"{benign:,}")
        col3.metric("Attacks Detected", f"{attacks:,}",
                    delta=f"{attacks/total*100:.1f}%", delta_color="inverse")

        st.divider()
        st.subheader("Attack Type Breakdown")
        st.bar_chart(pd.Series(labels).value_counts())

        st.divider()
        st.subheader("Sample Predictions")
        df_out = df.copy()
        df_out['prediction'] = labels
        st.dataframe(df_out[['prediction']].join(df.select_dtypes(include=[np.number]).iloc[:, :5]))

        st.divider()
        csv = df_out.to_csv(index=False).encode()
        st.download_button("Download Results CSV", csv, "results.csv", "text/csv")
