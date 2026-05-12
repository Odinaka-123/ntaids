import numpy as np
import os
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix

def build_lstm(input_dim, num_classes):
    model = keras.Sequential([
        layers.Input(shape=(1, input_dim)),
        layers.LSTM(128, return_sequences=True),
        layers.Dropout(0.3),
        layers.LSTM(64),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ], name='lstm_ids')

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    model.summary()
    return model

def reshape_for_lstm(X):
    """LSTM expects 3D input: (samples, timesteps, features)"""
    return X.reshape((X.shape[0], 1, X.shape[1]))

def train_lstm(X_train, y_train, X_test, y_test, num_classes, epochs=20, batch_size=256):
    print("Training LSTM...")
    input_dim = X_train.shape[1]

    X_train_r = reshape_for_lstm(X_train)
    X_test_r  = reshape_for_lstm(X_test)

    model = build_lstm(input_dim, num_classes)

    history = model.fit(
        X_train_r, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_test_r, y_test),
        verbose=1
    )
    print("LSTM training complete.")
    return model, history

def evaluate(model, X_test, y_test, label_names=None):
    X_test_r = reshape_for_lstm(X_test)
    y_pred = np.argmax(model.predict(X_test_r), axis=1)
    print("\n--- LSTM Results ---")
    print(classification_report(y_test, y_pred, target_names=label_names))
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:\n", cm)
    return y_pred, cm

def save_model(model, path='results/lstm_model'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    model.save(path)
    print(f"Model saved to {path}")

def load_model(path='results/lstm_model'):
    return keras.models.load_model(path)