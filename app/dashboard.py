import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
sys.path.append('..')

from src.features import engineer_features
from src.models.lstm import reshape_for_lstm
from tensorflow import keras

st.set_page_config(page_title="NTA-IDS Dashboard", layout="wide")
st.title("NTA-IDS — Network Intrusion Detection System")
st.markdown("Upload a CSV of network flow records to detect intrusions.")

# --- Load models ---
@st.cache_resource
def load_models():
    models = {}
    try:
        models['rf']     = joblib.load('results/rf_model.pkl')
        models['svm']    = joblib.load('results/svm_model.pkl')
        models['lstm']   = keras.models.load_model('results/lstm_model')
        models['scaler'] = joblib.load('results/scaler.pkl')
        models['pca']    = joblib.load('results/pca.pkl')
        models['le']     = joblib.load('results/label_encoder.pkl')
        return models, None
    except Exception as e:
        return None, str(e)

models, error = load_models()

if error:
    st.warning(f"Models not loaded yet: {error}")
    st.info("Train the models first by running the main pipeline notebook.")
else:
    st.success("All models loaded successfully.")

# --- File upload ---
st.divider()
uploaded = st.file_uploader("Upload network flow CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded, low_memory=False)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    st.write(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
    st.dataframe(df.head())

    if models and st.button("Run Detection"):
        with st.spinner("Analysing traffic..."):
            # Preprocess
            df = engineer_features(df)
            X = df.select_dtypes(include=[np.number])
            X_scaled = models['scaler'].transform(X)
            X_pca    = models['pca'].transform(X_scaled)

            # Predictions
            rf_proba   = models['rf'].predict_proba(X_pca)
            svm_proba  = models['svm'].predict_proba(X_pca)
            lstm_proba = models['lstm'].predict(reshape_for_lstm(X_pca))

            # Weighted ensemble
            avg = (0.3 * rf_proba) + (0.2 * svm_proba) + (0.5 * lstm_proba)
            preds = np.argmax(avg, axis=1)
            labels = models['le'].inverse_transform(preds)

        # Results
        st.divider()
        st.subheader("Detection Results")

        df_out = df.copy()
        df_out['prediction'] = labels

        total    = len(labels)
        benign   = (labels == 'BENIGN').sum()
        attacks  = total - benign

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Flows",    f"{total:,}")
        col2.metric("Benign",         f"{benign:,}")
        col3.metric("Attacks Detected", f"{attacks:,}",
                    delta=f"{attacks/total*100:.1f}%",
                    delta_color="inverse")

        # Attack breakdown
        attack_counts = pd.Series(labels).value_counts()
        st.bar_chart(attack_counts)

        # Full table
        st.dataframe(df_out[['prediction']].join(df.select_dtypes(include=[np.number]).iloc[:, :5]))

        # Download results
        csv = df_out.to_csv(index=False).encode()
        st.download_button("Download Results CSV", csv, "results.csv", "text/csv")