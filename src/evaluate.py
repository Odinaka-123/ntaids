import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, roc_auc_score, confusion_matrix
)


def compute_metrics(y_test, y_pred, model_name='model'):
    acc  = accuracy_score(y_test, y_pred)
    f1   = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec  = recall_score(y_test, y_pred, average='weighted', zero_division=0)

    # False positive rate
    cm  = confusion_matrix(y_test, y_pred)
    fp  = cm.sum(axis=0) - np.diag(cm)
    tn  = cm.sum() - (cm.sum(axis=1) + cm.sum(axis=0) - np.diag(cm))
    fpr = np.mean(fp / (fp + tn + 1e-6))

    metrics = {
        'model':     model_name,
        'accuracy':  round(acc,  4),
        'f1_score':  round(f1,   4),
        'precision': round(prec, 4),
        'recall':    round(rec,  4),
        'fpr':       round(fpr,  4),
    }

    print(f"\n[{model_name}] Accuracy: {acc:.4f} | F1: {f1:.4f} | "
          f"Precision: {prec:.4f} | Recall: {rec:.4f} | FPR: {fpr:.4f}")
    return metrics


def plot_confusion_matrix(y_test, y_pred, label_names, model_name='model', save_dir='results'):
    os.makedirs(save_dir, exist_ok=True)
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=label_names, yticklabels=label_names)
    plt.title(f'Confusion Matrix — {model_name}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    path = os.path.join(save_dir, f'cm_{model_name.lower().replace(" ", "_")}.png')
    plt.savefig(path)
    plt.close()
    print(f"Saved confusion matrix to {path}")


def plot_training_history(history, model_name='LSTM', save_dir='results'):
    os.makedirs(save_dir, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(history.history['accuracy'],     label='Train')
    ax1.plot(history.history['val_accuracy'], label='Val')
    ax1.set_title('Accuracy')
    ax1.set_xlabel('Epoch')
    ax1.legend()

    ax2.plot(history.history['loss'],     label='Train')
    ax2.plot(history.history['val_loss'], label='Val')
    ax2.set_title('Loss')
    ax2.set_xlabel('Epoch')
    ax2.legend()

    plt.suptitle(f'{model_name} Training History')
    plt.tight_layout()
    path = os.path.join(save_dir, f'history_{model_name.lower()}.png')
    plt.savefig(path)
    plt.close()
    print(f"Saved training history to {path}")


def compare_models(metrics_list, save_dir='results'):
    """Bar chart comparing all models side by side."""
    os.makedirs(save_dir, exist_ok=True)
    names   = [m['model']    for m in metrics_list]
    acc     = [m['accuracy'] for m in metrics_list]
    f1      = [m['f1_score'] for m in metrics_list]
    fpr     = [m['fpr']      for m in metrics_list]

    x = np.arange(len(names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, acc, width, label='Accuracy')
    ax.bar(x,         f1,  width, label='F1 Score')
    ax.bar(x + width, fpr, width, label='FPR')

    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylim(0, 1.1)
    ax.set_title('Model Comparison')
    ax.legend()
    plt.tight_layout()
    path = os.path.join(save_dir, 'model_comparison.png')
    plt.savefig(path)
    plt.close()
    print(f"Saved model comparison chart to {path}")