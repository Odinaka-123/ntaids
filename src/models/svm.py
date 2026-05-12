import joblib
import os
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix

def train_svm(X_train, y_train, kernel='rbf', C=1.0, random_state=42):
    print("Training SVM...")
    model = SVC(
        kernel=kernel,
        C=C,
        random_state=random_state,
        class_weight='balanced',
        probability=True
    )
    model.fit(X_train, y_train)
    print("SVM training complete.")
    return model

def evaluate(model, X_test, y_test, label_names=None):
    y_pred = model.predict(X_test)
    print("\n--- SVM Results ---")
    print(classification_report(y_test, y_pred, target_names=label_names))
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:\n", cm)
    return y_pred, cm

def save_model(model, path='results/svm_model.pkl'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"Model saved to {path}")

def load_model(path='results/svm_model.pkl'):
    return joblib.load(path)