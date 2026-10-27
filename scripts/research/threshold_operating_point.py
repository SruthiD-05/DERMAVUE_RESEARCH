"""Validation-only threshold selection followed by one frozen test report."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score,
                             balanced_accuracy_score, brier_score_loss,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)


THRESHOLDS = [round(value, 2) for value in np.arange(0.10, 0.901, 0.05)]


def _specificity(y_true, y_pred) -> float:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return float(tn / (tn + fp)) if tn + fp else 0.0


def _ece(y_true, probabilities, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    predictions = probabilities >= 0.5
    confidence = np.where(predictions, probabilities, 1.0 - probabilities)
    correctness = predictions == y_true
    total = len(y_true)
    value = 0.0
    for low, high in zip(edges[:-1], edges[1:]):
        selected = (confidence >= low) & (confidence <= high if high == 1 else confidence < high)
        if selected.any():
            value += selected.sum() / total * abs(float(correctness[selected].mean()) - float(confidence[selected].mean()))
    return float(value)


def _metrics(y_true, probabilities, threshold: float) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "macro_f1": float(f1_score(y_true, predictions, average="macro", zero_division=0)),
        "precision_melanoma": float(precision_score(y_true, predictions, zero_division=0)),
        "melanoma_sensitivity": float(recall_score(y_true, predictions, zero_division=0)),
        "melanoma_specificity": _specificity(y_true, predictions),
        "auroc": float(roc_auc_score(y_true, probabilities)),
        "auprc": float(average_precision_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "expected_calibration_error": _ece(y_true, probabilities),
        "false_negatives": int(fn),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "true_positives": int(tp),
        "n": int(len(y_true)),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _joined(manifest_path: Path, predictions_path: Path) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_path)
    predictions = pd.read_csv(predictions_path)
    if "split" in manifest.columns and len(set(manifest["split"])) != 1:
        raise ValueError(f"{manifest_path} must contain exactly one declared split.")
    repeated = (set(manifest.columns) & set(predictions.columns)) - {"image_id"}
    predictions = predictions.drop(columns=sorted(repeated), errors="ignore")
    frame = manifest.merge(predictions, on="image_id", how="inner", validate="one_to_one").sort_values("image_id").reset_index(drop=True)
    if len(frame) != len(manifest):
        raise ValueError(f"Predictions do not cover {manifest_path}.")
    required = {"binary_label", "probability_melanoma", "image_id"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Joined data is missing: {', '.join(missing)}")
    return frame


def _group_bootstrap(frame: pd.DataFrame, threshold: float, seed: int, repeats: int = 1000) -> dict:
    group_column = "lesion_id" if "lesion_id" in frame.columns else None
    rng = np.random.default_rng(seed)
    values = {"accuracy": [], "melanoma_sensitivity": [], "melanoma_specificity": [], "macro_f1": []}
    if group_column:
        group_codes, groups = pd.factorize(frame[group_column], sort=False)
        labels = frame["binary_label"].astype(int).to_numpy()
        predictions = (frame["probability_melanoma"].astype(float).to_numpy() >= threshold).astype(int)
        group_confusions = np.zeros((len(groups), 4), dtype=np.int64)
        for code in range(len(groups)):
            selected = group_codes == code
            matrix = confusion_matrix(labels[selected], predictions[selected], labels=[0, 1]).ravel()
            group_confusions[code] = matrix
        for _ in range(repeats):
            sampled = rng.choice(groups, size=len(groups), replace=True)
            sampled_codes = pd.Index(groups).get_indexer(sampled)
            tn, fp, fn, tp = group_confusions[sampled_codes].sum(axis=0)
            total = tn + fp + fn + tp
            sensitivity = tp / (tp + fn) if tp + fn else 0.0
            specificity = tn / (tn + fp) if tn + fp else 0.0
            f1_negative = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
            f1_positive = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
            for name, value in {
                "accuracy": (tn + tp) / total if total else 0.0,
                "melanoma_sensitivity": sensitivity,
                "melanoma_specificity": specificity,
                "macro_f1": (f1_negative + f1_positive) / 2,
            }.items():
                values[name].append(float(value))
    else:
        indices = np.arange(len(frame))
        for _ in range(repeats):
            sample = frame.iloc[rng.choice(indices, size=len(indices), replace=True)]
            result = _metrics(sample["binary_label"].to_numpy(), sample["probability_melanoma"].to_numpy(), threshold)
            for name in values:
                values[name].append(result[name])
    return {name: [float(np.quantile(items, 0.025)), float(np.quantile(items, 0.975))] for name, items in values.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-manifest", type=Path, required=True)
    parser.add_argument("--validation-predictions", type=Path, required=True)
    parser.add_argument("--test-manifest", type=Path, required=True)
    parser.add_argument("--test-predictions", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--min-validation-specificity", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        validation = _joined(args.validation_manifest, args.validation_predictions)
        test = _joined(args.test_manifest, args.test_predictions)
        validation_probabilities = validation["probability_melanoma"].astype(float).to_numpy()
        validation_labels = validation["binary_label"].astype(int).to_numpy()
        validation_rows = [_metrics(validation_labels, validation_probabilities, threshold) for threshold in THRESHOLDS]
        validation_table = pd.DataFrame(validation_rows)
        eligible = validation_table[validation_table["melanoma_specificity"] >= args.min_validation_specificity]
        if eligible.empty:
            raise ValueError("No declared threshold meets the validation specificity constraint.")
        selected = eligible.sort_values(
            ["melanoma_sensitivity", "melanoma_specificity", "threshold"],
            ascending=[False, False, True],
        ).iloc[0]
        selected_threshold = float(selected["threshold"])
        test_labels = test["binary_label"].astype(int).to_numpy()
        test_probabilities = test["probability_melanoma"].astype(float).to_numpy()
        test_metrics = _metrics(test_labels, test_probabilities, selected_threshold)
        test_metrics["bootstrap_95ci_grouped_by_lesion"] = _group_bootstrap(test, selected_threshold, args.seed)
        test_metrics["data_provenance"] = "genuine"
        test_metrics["task"] = "binary_melanoma_other_dx_v1"
        test_metrics["selection_data"] = str(args.validation_manifest.resolve())
        test_metrics["test_manifest"] = str(args.test_manifest.resolve())
        test_metrics["test_used_for_threshold_selection"] = False

        args.out_dir.mkdir(parents=True, exist_ok=True)
        validation_table.to_csv(args.out_dir / "validation_threshold_table.csv", index=False)
        test_output = test[["image_id", "lesion_id", "binary_label", "probability_melanoma"]].copy()
        test_output["predicted_label"] = (test_output["probability_melanoma"] >= selected_threshold).astype(int)
        test_output.to_csv(args.out_dir / "test_operating_point_predictions.csv", index=False)
        (args.out_dir / "test_operating_point_metrics.json").write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
        protocol = {
            "threshold_grid": THRESHOLDS,
            "selection_rule": "maximize validation melanoma sensitivity subject to validation specificity >= configured minimum; ties specificity then lower threshold",
            "minimum_validation_specificity": args.min_validation_specificity,
            "selected_threshold": selected_threshold,
            "validation_manifest_sha256": _sha256(args.validation_manifest),
            "test_manifest_sha256": _sha256(args.test_manifest),
            "test_used_for_threshold_selection": False,
            "group_bootstrap": "lesion_id when available",
        }
        (args.out_dir / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
        print(json.dumps({"selected_threshold": selected_threshold, "validation_selection": selected.to_dict(), "test_metrics": test_metrics}, indent=2, default=str))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"THRESHOLD ANALYSIS BLOCKED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
