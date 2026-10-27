"""Evaluate predictions against a frozen genuine-data test manifest only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix,
                             average_precision_score, f1_score,
                             precision_recall_fscore_support, recall_score,
                             roc_auc_score)
from sklearn.preprocessing import label_binarize

LABELS = [
    "Normal Skin", "Skin Allergy/Acne", "Suspicious Lesion",
    "Possible Skin Cancer (Basal Cell Carcinoma)", "Possible Skin Cancer (Melanoma)",
]
TASK_LABELS = {
    "ham10000_five_class": LABELS,
    "binary_benign_melanoma": ["Benign", "Melanoma"],
    "binary_melanoma_other_dx_v1": ["Non-melanoma (other HAM10000 dx)", "Melanoma"],
}


def evaluate(manifest: pd.DataFrame, predictions: pd.DataFrame, task: str = "ham10000_five_class") -> dict:
    if task not in TASK_LABELS:
        raise ValueError(f"Unsupported task: {task}")
    labels = TASK_LABELS[task]
    label_column = "risk_label" if task == "ham10000_five_class" else "binary_label"
    if "image_id" not in predictions.columns or "predicted_label" not in predictions.columns:
        raise ValueError("Predictions CSV requires image_id and predicted_label columns.")
    if predictions["image_id"].duplicated().any():
        raise ValueError("Predictions contain duplicate image_id values.")
    # Labels and metadata must come from the frozen manifest. Prediction files
    # may repeat them for traceability, but repeated columns must not create
    # ambiguous ``*_x``/``*_y`` fields or let prediction-side labels enter the
    # evaluation.
    repeated = (set(manifest.columns) & set(predictions.columns)) - {"image_id"}
    predictions_for_merge = predictions.drop(columns=sorted(repeated), errors="ignore")
    joined = manifest.merge(predictions_for_merge, on="image_id", how="left", validate="one_to_one")
    if joined["predicted_label"].isna().any():
        raise ValueError("Predictions do not cover every test-manifest image.")
    if "split" in joined.columns and set(joined["split"]) != {"test"}:
        raise ValueError("Evaluation manifest must contain test rows only.")
    if label_column not in joined.columns:
        raise ValueError(f"Manifest must contain {label_column} for task {task}.")
    # Keep labels, predictions, and probabilities in the same deterministic
    # image_id order before computing any metric.
    joined = joined.sort_values("image_id").reset_index(drop=True)
    y_true = joined[label_column].astype(int).to_numpy()
    y_pred = joined["predicted_label"].astype(int).to_numpy()
    class_indices = np.arange(len(labels))
    if not np.isin(y_true, class_indices).all() or not np.isin(y_pred, class_indices).all():
        raise ValueError("predicted_label contains an unknown class index.")
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=class_indices, zero_division=0)
    matrix = confusion_matrix(y_true, y_pred, labels=class_indices)
    specificities = []
    for index in class_indices:
        true_negative = matrix.sum() - (matrix[index, :].sum() + matrix[:, index].sum() - matrix[index, index])
        false_positive = matrix[:, index].sum() - matrix[index, index]
        specificities.append(true_negative / (true_negative + false_positive) if true_negative + false_positive else 0.0)
    result = {
        "data_provenance": "genuine",
        "task": task,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "macro_sensitivity": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_specificity": float(np.mean(specificities)),
        "per_class": {labels[i]: {"precision": float(precision[i]), "sensitivity": float(recall[i]), "specificity": float(specificities[i]), "f1": float(f1[i]), "support": int(support[i])} for i in range(len(labels))},
        "confusion_matrix": matrix.tolist(),
        "class_distribution": pd.Series(y_true).value_counts().sort_index().astype(int).to_dict(),
        "test_samples": int(len(y_true)),
        "target_accuracy": 0.9,
        "target_reached": bool(accuracy_score(y_true, y_pred) >= 0.9),
    }
    probability_columns = [f"probability_{index}" for index in class_indices]
    if all(column in predictions.columns for column in probability_columns):
        ordered = joined.filter(regex=r"^probability_[0-9]+$").to_numpy()
        try:
            if len(labels) == 2:
                result["auroc"] = float(roc_auc_score(y_true, ordered[:, 1]))
                result["auprc"] = float(average_precision_score(y_true, ordered[:, 1]))
            else:
                ordered_true = label_binarize(y_true, classes=class_indices)
                result["macro_auroc"] = float(roc_auc_score(y_true, ordered, multi_class="ovr", average="macro", labels=class_indices))
                result["macro_auprc"] = float(average_precision_score(ordered_true, ordered, average="macro"))
        except ValueError:
            result["auroc"] = None if len(labels) == 2 else result.get("macro_auroc")
            result["auprc"] = None if len(labels) == 2 else result.get("macro_auprc")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--data-provenance", choices=["genuine"], required=True)
    parser.add_argument("--task", choices=sorted(TASK_LABELS), default="ham10000_five_class")
    args = parser.parse_args()
    try:
        manifest = pd.read_csv(args.manifest)
        source_text = " ".join(manifest.astype(str).fillna("").to_numpy().ravel()).lower()
        if any(marker in source_text for marker in ("synthetic", "demo_dataset", "demo")):
            raise ValueError("Synthetic/demo manifests are not eligible for genuine evaluation.")
        result = evaluate(manifest, pd.read_csv(args.predictions), args.task)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"EVALUATION BLOCKED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
