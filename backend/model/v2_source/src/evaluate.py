"""
evaluate.py
-----------
Step 6 of the methodology: evaluate the classifier with standard metrics
AND disaggregated by skin-tone group. This is the concrete implementation
of the research-gap fix identified in the literature survey -- reporting
one aggregate accuracy number hides exactly the failure mode (poorer
performance on underrepresented skin tones) that this project set out to
address.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)


def compute_metrics(y_true, y_pred, y_prob):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "sensitivity_recall": recall_score(y_true, y_pred, zero_division=0),
        "specificity": _specificity(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "auc": roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else float("nan"),
        "n": len(y_true),
    }


def _specificity(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    return tn / (tn + fp) if (tn + fp) > 0 else float("nan")


def evaluate_overall_and_stratified(y_true, y_pred, y_prob, groups, group_name="skin_tone"):
    """
    Returns:
        overall: dict of metrics on the full test set
        by_group: DataFrame, one row per group, same metrics + group size
    """
    overall = compute_metrics(y_true, y_pred, y_prob)

    rows = []
    for g in sorted(set(groups)):
        idx = groups == g
        if idx.sum() == 0:
            continue
        m = compute_metrics(y_true[idx], y_pred[idx], y_prob[idx])
        m[group_name] = g
        rows.append(m)
    by_group = pd.DataFrame(rows).set_index(group_name) if rows else pd.DataFrame()
    return overall, by_group


def fairness_gap(by_group_df, metric="accuracy"):
    """Max - min of a metric across skin-tone groups: the key number for the
    research-gap discussion. A large gap means the model is not performing
    equitably across skin tones, even if aggregate accuracy looks good."""
    if by_group_df.empty or metric not in by_group_df:
        return float("nan")
    return float(by_group_df[metric].max() - by_group_df[metric].min())


# ---------------------------------------------------------------------------
# Multiclass variants, used by the real-data 5-class pipeline (train_real.py).
# Kept separate from the binary functions above so the synthetic-data demo
# pipeline (train.py) is untouched.
# ---------------------------------------------------------------------------

def compute_metrics_multiclass(y_true, y_pred, y_prob, n_classes):
    """y_prob: (n_samples, n_classes) predicted probabilities.
    Precision/recall/f1/specificity are macro-averaged across classes;
    'sensitivity_recall' here is the macro-recall (mean per-class recall),
    the multiclass analogue of binary sensitivity."""
    labels = list(range(n_classes))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    specs = []
    for i in labels:
        tn = cm.sum() - (cm[i, :].sum() + cm[:, i].sum() - cm[i, i])
        fp = cm[:, i].sum() - cm[i, i]
        specs.append(tn / (tn + fp) if (tn + fp) > 0 else float("nan"))

    try:
        auc = roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro", labels=labels)
    except ValueError:
        auc = float("nan")  # e.g. a class missing entirely from this split

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "sensitivity_recall": recall_score(y_true, y_pred, average="macro", zero_division=0, labels=labels),
        "specificity": float(np.nanmean(specs)),
        "precision": precision_score(y_true, y_pred, average="macro", zero_division=0, labels=labels),
        "f1": f1_score(y_true, y_pred, average="macro", zero_division=0, labels=labels),
        "auc": auc,
        "n": len(y_true),
    }


def evaluate_overall_and_stratified_multiclass(y_true, y_pred, y_prob, groups, n_classes, group_name="skin_tone_proxy"):
    overall = compute_metrics_multiclass(y_true, y_pred, y_prob, n_classes)

    rows = []
    for g in sorted(set(groups)):
        idx = groups == g
        if idx.sum() == 0:
            continue
        # A group needs at least one sample of >=2 classes for AUC to be
        # defined; compute_metrics_multiclass already guards that internally.
        m = compute_metrics_multiclass(y_true[idx], y_pred[idx], y_prob[idx], n_classes)
        m[group_name] = g
        rows.append(m)
    by_group = pd.DataFrame(rows).set_index(group_name) if rows else pd.DataFrame()
    return overall, by_group


def per_class_report(y_true, y_pred, class_names):
    """Precision/recall/f1/support broken out per risk category -- more
    actionable than the macro-averaged numbers alone, e.g. to see whether
    melanoma specifically is being under-detected."""
    from sklearn.metrics import classification_report
    report = classification_report(
        y_true, y_pred, labels=list(range(len(class_names))),
        target_names=class_names, output_dict=True, zero_division=0,
    )
    return pd.DataFrame(report).transpose()
