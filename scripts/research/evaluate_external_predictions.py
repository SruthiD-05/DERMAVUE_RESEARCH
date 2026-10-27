"""Evaluate predictions on a frozen, patient-grouped external manifest.

This evaluator is intentionally separate from the HAM10000 evaluator.  It
requires a genuine-external manifest, refuses synthetic/demo provenance, and
records hashes and configuration needed to reproduce a single frozen run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             confusion_matrix, f1_score, precision_score, recall_score,
                             precision_recall_fscore_support, roc_auc_score)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact_hash(path: Path) -> str:
    if path.is_file():
        return _sha256(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    for child in sorted(path.rglob("*")):
        if child.is_file():
            digest.update(str(child.relative_to(path)).replace("\\", "/").encode())
            digest.update(bytes.fromhex(_sha256(child)))
    return digest.hexdigest()


def _require_completed_overlap_review(review_path: Path) -> dict:
    if not review_path.is_file():
        raise FileNotFoundError(review_path)
    report = json.loads(review_path.read_text(encoding="utf-8"))
    counts = report.get("disposition_counts", {})
    if report.get("report_status") not in {"complete", "review_complete"}:
        raise ValueError("External evaluation blocked until the HAM/ISIC overlap review is complete")
    if int(counts.get("unreviewed", 0)) or int(counts.get("uncertain", 0)):
        raise ValueError("External evaluation blocked while overlap candidates remain unreviewed or uncertain")
    return report


def _ece(y_true: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (probability >= left) & (probability <= right if right == 1.0 else probability < right)
        if mask.any():
            total += float(mask.mean()) * abs(float(y_true[mask].mean()) - float(probability[mask].mean()))
    return total


def _point_metrics(y_true: np.ndarray, probability: np.ndarray, threshold: float) -> dict:
    y_pred = (probability >= threshold).astype(int)
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    per_class_precision, per_class_recall, per_class_f1, per_class_support = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1], zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "per_class_metrics": {
            "0": {"precision": float(per_class_precision[0]), "sensitivity": float(per_class_recall[0]), "f1": float(per_class_f1[0]), "support": int(per_class_support[0])},
            "1": {"precision": float(per_class_precision[1]), "sensitivity": float(per_class_recall[1]), "f1": float(per_class_f1[1]), "support": int(per_class_support[1])},
        },
        "auroc": float(roc_auc_score(y_true, probability)) if len(np.unique(y_true)) == 2 else None,
        "auprc": float(average_precision_score(y_true, probability)) if len(np.unique(y_true)) == 2 else None,
        "brier_score": float(brier_score_loss(y_true, probability)),
        "expected_calibration_error": float(_ece(y_true, probability)),
        "confusion_matrix": matrix.tolist(),
        "positive_support": int(tp + fn),
        "negative_support": int(tn + fp),
        "false_negatives": int(fn),
        "false_positives": int(fp),
    }


def _bootstrap(frame: pd.DataFrame, probability: np.ndarray, threshold: float, seed: int, iterations: int) -> dict:
    groups = frame["patient_id"].astype(str).to_numpy()
    unique = np.unique(groups)
    indices = {group: np.flatnonzero(groups == group) for group in unique}
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(iterations):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        rows = np.concatenate([indices[group] for group in sampled])
        values.append(_point_metrics(frame["external_binary_label"].to_numpy()[rows], probability[rows], threshold))
    output = {}
    for key in ("accuracy", "sensitivity", "specificity", "precision", "f1", "auroc", "auprc"):
        numbers = np.asarray([value[key] for value in values if value[key] is not None], dtype=float)
        output[key] = {
            "lower_2.5_percent": float(np.quantile(numbers, 0.025)),
            "upper_97.5_percent": float(np.quantile(numbers, 0.975)),
        } if len(numbers) else None
    return output


def evaluate(manifest_path: Path, predictions_path: Path, checkpoint: Path, config_path: Path | None, threshold: float, seed: int, bootstrap_iterations: int, overlap_review_path: Path) -> dict:
    manifest = pd.read_csv(manifest_path)
    required = {"image_id", "patient_id", "external_binary_label", "split", "data_provenance"}
    missing = sorted(required - set(manifest.columns))
    if missing:
        raise ValueError(f"External manifest is missing columns: {missing}")
    if set(manifest["split"].astype(str)) != {"external_evaluation"}:
        raise ValueError("External evaluation requires only rows marked external_evaluation")
    if set(manifest["data_provenance"].astype(str)) != {"genuine_external"}:
        raise ValueError("External evaluation requires genuine_external provenance")
    review_report = _require_completed_overlap_review(overlap_review_path)
    if manifest["image_id"].duplicated().any() or manifest["patient_id"].isna().any():
        raise ValueError("External manifest image IDs must be unique and patient IDs complete")
    predictions = pd.read_csv(predictions_path)
    if predictions["image_id"].duplicated().any():
        raise ValueError("External predictions contain duplicate image IDs")
    for column in ("image_id", "probability_1"):
        if column not in predictions.columns:
            raise ValueError(f"External predictions require {column}")
    joined = manifest.merge(predictions[["image_id", "probability_1"]], on="image_id", how="left", validate="one_to_one")
    if joined["probability_1"].isna().any():
        raise ValueError("Predictions do not cover every external manifest row")
    joined = joined.sort_values("image_id").reset_index(drop=True)
    y_true = joined["external_binary_label"].astype(int).to_numpy()
    probability = joined["probability_1"].astype(float).to_numpy()
    if not np.isfinite(probability).all() or not ((probability >= 0.0) & (probability <= 1.0)).all():
        raise ValueError("probability_1 must be finite and within [0, 1]")
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path else None
    if config is not None:
        if config.get("task") != "isic2020_melanoma_vs_nonmelanoma_v1":
            raise ValueError("Evaluation config does not declare the ISIC V2 task")
        if config.get("label_mapping") != {"0": "official non-melanoma", "1": "melanoma"}:
            raise ValueError("Evaluation config label mapping does not match the official task contract")
    result = _point_metrics(y_true, probability, threshold)
    result.update({
        "data_provenance": "genuine_external",
        "task": config["task"] if config else "isic2020_melanoma_vs_nonmelanoma_v1",
        "dataset_id": str(manifest["dataset_id"].iloc[0]) if "dataset_id" in manifest else "unknown",
        "dataset_version": str(manifest["dataset_version"].iloc[0]) if "dataset_version" in manifest else "unknown",
        "manifest_sha256": _sha256(manifest_path),
        "prediction_sha256": _sha256(predictions_path),
        "model_artifact_sha256": _artifact_hash(checkpoint),
        "model_artifact_path": str(checkpoint.resolve()),
        "config_sha256": _sha256(config_path) if config_path else None,
        "threshold": threshold,
        "n_images": int(len(joined)),
        "n_patients": int(joined["patient_id"].nunique()),
        "class_distribution": joined["external_binary_label"].value_counts().sort_index().astype(int).to_dict(),
        "bootstrap_group": "patient_id",
        "bootstrap_seed": seed,
        "bootstrap_iterations": bootstrap_iterations,
        "bootstrap_95ci": _bootstrap(joined, probability, threshold, seed, bootstrap_iterations),
        "evaluation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "software": {"python": platform.python_version(), "platform": platform.platform()},
        "test_set_used_for_selection": False,
        "clinical_validation": False,
        "overlap_review_report": str(overlap_review_path.resolve()),
        "overlap_review_report_sha256": _sha256(overlap_review_path),
        "overlap_review_status": review_report["report_status"],
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--overlap-review-report", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    args = parser.parse_args()
    try:
        result = evaluate(args.manifest, args.predictions, args.checkpoint, args.config, args.threshold, args.seed, args.bootstrap_iterations, args.overlap_review_report)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"EXTERNAL EVALUATION BLOCKED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
