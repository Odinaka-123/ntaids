import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from src.models.lstm import reshape_for_lstm


def predict_all(rf_model, svm_model, lstm_model, X_test):
    """Get predictions from all three models."""
    rf_proba   = rf_model.predict_proba(X_test)
    svm_proba  = svm_model.predict_proba(X_test)
    lstm_proba = lstm_model.predict(reshape_for_lstm(X_test))
    return rf_proba, svm_proba, lstm_proba


def hard_vote(rf_proba, svm_proba, lstm_proba):
    """Majority voting across three models."""
    rf_pred   = np.argmax(rf_proba,   axis=1)
    svm_pred  = np.argmax(svm_proba,  axis=1)
    lstm_pred = np.argmax(lstm_proba, axis=1)

    # Stack predictions and take majority vote per sample
    stacked = np.stack([rf_pred, svm_pred, lstm_pred], axis=1)
    final   = np.apply_along_axis(
        lambda x: np.bincount(x).argmax(), axis=1, arr=stacked
    )
    return final


def weighted_vote(rf_proba, svm_proba, lstm_proba, weights=(0.3, 0.2, 0.5)):
    """Weighted average of predicted probabilities.
    Default: LSTM gets highest weight for sequential pattern detection.
    """
    w_rf, w_svm, w_lstm = weights
    avg_proba = (w_rf * rf_proba) + (w_svm * svm_proba) + (w_lstm * lstm_proba)
    return np.argmax(avg_proba, axis=1)


def evaluate_ensemble(y_pred, y_test, method='ensemble', label_names=None):
    print(f"\n--- {method.upper()} Results ---")
    print(classification_report(y_test, y_pred, target_names=label_names))
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:\n", cm)
    return cm


def run_ensemble(rf_model, svm_model, lstm_model, X_test, y_test,
                 weights=(0.3, 0.2, 0.5), label_names=None):
    rf_proba, svm_proba, lstm_proba = predict_all(
        rf_model, svm_model, lstm_model, X_test
    )

    print("\nRunning hard voting...")
    hard_pred = hard_vote(rf_proba, svm_proba, lstm_proba)
    evaluate_ensemble(hard_pred, y_test, method='hard vote', label_names=label_names)

    print("\nRunning weighted voting...")
    weighted_pred = weighted_vote(rf_proba, svm_proba, lstm_proba, weights)
    evaluate_ensemble(weighted_pred, y_test, method='weighted vote', label_names=label_names)

    return hard_pred, weighted_pred