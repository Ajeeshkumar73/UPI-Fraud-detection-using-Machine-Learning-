import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, auc, confusion_matrix, roc_curve
)

def evaluate_model_performance(y_true, y_pred, y_prob):
    """
    Computes comprehensive evaluation metrics for binary classification.
    Returns dictionary with all metrics and curve coordinates.
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    try:
        roc_auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        roc_auc = 0.5
        
    p_curve, r_curve, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = float(auc(r_curve, p_curve))
    
    cm = confusion_matrix(y_true, y_pred).tolist() # [[tn, fp], [fn, tp]]
    
    # Calculate ROC curve points (downsampled for JSON storage)
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    step = max(1, len(fpr) // 50)
    roc_points = [{"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)} for i in range(0, len(fpr), step)]
    
    # Calculate PR curve points (downsampled)
    pr_step = max(1, len(p_curve) // 50)
    pr_points = [{"precision": round(float(p_curve[i]), 4), "recall": round(float(r_curve[i]), 4)} for i in range(0, len(p_curve), pr_step)]

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "confusion_matrix": cm,
        "roc_curve": roc_points,
        "pr_curve": pr_points
    }
