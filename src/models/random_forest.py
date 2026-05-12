import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

def train_random_forest(X_train, y_train, n_estimators=100, random_state=42):
    print("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)
    print("Random Forest training complete.")
    return model

def evaluate(model, X_test, y_test, label_names=None):
    y_pred = model.predict(X_test)
    print("\n--- Random Forest Results ---")
    print(classification_report(y_test, y_pred, target_names=label_names))
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:\n", cm)
    return y_pred, cm

def get_feature_importance(model, feature_names):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    print("\nTop 20 features:")
    for i in range(min(20, len(feature_names))):
        print(f"  {i+1}. {feature_names[indices[i]]}: {importances[indices[i]]:.4f}")
    return importances, indices

def save_model(model, path='results/rf_model.pkl'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"Model saved to {path}")

def load_model(path='results/rf_model.pkl'):
    return joblib.load(path)