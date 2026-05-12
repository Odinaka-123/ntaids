import numpy as np
from sklearn.decomposition import PCA
from tensorflow import keras
from tensorflow.keras import layers
import joblib
import os

# --- PCA ---

def apply_pca(X_train, X_test, variance_threshold=0.95):
    """Reduce dimensions keeping enough components for 95% variance."""
    pca = PCA(n_components=variance_threshold, random_state=42)
    X_train_pca = pca.fit_transform(X_train)
    X_test_pca  = pca.transform(X_test)
    print(f"PCA: {X_train.shape[1]} features → {X_train_pca.shape[1]} components "
          f"({variance_threshold*100:.0f}% variance retained)")
    return X_train_pca, X_test_pca, pca


# --- Autoencoder ---

def build_autoencoder(input_dim, encoding_dim=32):
    """Shallow autoencoder for unsupervised feature compression."""
    inp = keras.Input(shape=(input_dim,))
    encoded = layers.Dense(64, activation='relu')(inp)
    encoded = layers.Dense(encoding_dim, activation='relu')(encoded)
    decoded = layers.Dense(64, activation='relu')(encoded)
    decoded = layers.Dense(input_dim, activation='linear')(decoded)

    autoencoder = keras.Model(inp, decoded, name='autoencoder')
    encoder     = keras.Model(inp, encoded, name='encoder')

    autoencoder.compile(optimizer='adam', loss='mse')
    return autoencoder, encoder


def train_autoencoder(X_train, X_test, encoding_dim=32, epochs=20, batch_size=256):
    input_dim = X_train.shape[1]
    autoencoder, encoder = build_autoencoder(input_dim, encoding_dim)

    print(f"Training autoencoder: {input_dim} → {encoding_dim} dims")
    autoencoder.fit(
        X_train, X_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_test, X_test),
        verbose=1
    )

    X_train_enc = encoder.predict(X_train)
    X_test_enc  = encoder.predict(X_test)
    print(f"Autoencoder encoding done: shape {X_train_enc.shape}")
    return X_train_enc, X_test_enc, autoencoder, encoder


# --- Save / Load ---

def save_reducer(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if hasattr(obj, 'save'):
        obj.save(path)
    else:
        joblib.dump(obj, path)
    print(f"Saved to {path}")


def load_reducer(path):
    if path.endswith('.h5') or os.path.isdir(path):
        return keras.models.load_model(path)
    return joblib.load(path)