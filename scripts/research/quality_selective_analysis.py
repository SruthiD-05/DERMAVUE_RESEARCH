"""Descriptive quality and selective-prediction analysis for frozen predictions.

This script never changes model weights, thresholds, or selection. It reports
fixed risk-coverage points and quality/error associations on a declared test
manifest after the binary protocol is frozen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def _quality(path: Path) -> dict:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read genuine image: {path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return {
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "laplacian_variance": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "mean_intensity": float(gray.mean()),
        "intensity_std": float(gray.std()),
        "mean_saturation": float(hsv[:, :, 1].mean()),
        "clipped_fraction": float(((gray <= 2) | (gray >= 253)).mean()),
    }


def _risk_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for requested in np.linspace(0.1, 1.0, 10):
        count = max(1, int(round(len(frame) * requested)))
        retained = frame.sort_values("confidence", ascending=False).head(count)
        y_true = retained["binary_label"].to_numpy()
        y_pred = retained["predicted_label"].to_numpy()
        positives = (y_true == 1).sum()
        rows.append({
            "requested_coverage": float(requested),
            "actual_coverage": float(len(retained) / len(frame)),
            "retained_samples": int(len(retained)),
            "selective_risk_error_rate": float((y_true != y_pred).mean()),
            "selective_accuracy": float((y_true == y_pred).mean()),
            "melanoma_sensitivity_retained": float(((y_true == 1) & (y_pred == 1)).sum() / positives) if positives else None,
        })
    return pd.DataFrame(rows)


def analyze(manifest_path: Path, predictions_path: Path, out_dir: Path) -> dict:
    manifest = pd.read_csv(manifest_path)
    predictions = pd.read_csv(predictions_path)
    source_text = " ".join(manifest.astype(str).fillna("").to_numpy().ravel()).lower()
    if any(marker in source_text for marker in ("synthetic", "demo_dataset", "demo/", "demo\\")):
        raise ValueError("Synthetic/demo manifests are not eligible for research analysis.")
    required = {"image_id", "image_path", "binary_label", "split"}
    missing = sorted(required - set(manifest.columns))
    if missing:
        raise ValueError(f"Manifest missing required columns: {', '.join(missing)}")
    if set(manifest["split"]) != {"test"}:
        raise ValueError("Quality analysis requires a test-only manifest.")
    required_predictions = {"image_id", "predicted_label", "probability_melanoma"}
    missing = sorted(required_predictions - set(predictions.columns))
    if missing:
        raise ValueError(f"Predictions missing required columns: {', '.join(missing)}")
    frame = manifest.merge(predictions, on="image_id", how="inner", validate="one_to_one")
    if len(frame) != len(manifest):
        raise ValueError("Predictions do not cover the complete test manifest.")
    if "binary_label_x" in frame.columns:
        frame["binary_label"] = frame["binary_label_x"].astype(int)
    elif "binary_label" not in frame.columns:
        raise ValueError("Joined test data has no binary_label column.")
    quality_rows = [_quality(Path(path)) for path in frame["image_path"]]
    quality = pd.DataFrame(quality_rows, index=frame.index)
    frame = pd.concat([frame.reset_index(drop=True), quality.reset_index(drop=True)], axis=1)
    frame["confidence"] = np.maximum(frame["probability_melanoma"], 1.0 - frame["probability_melanoma"])
    frame["correct"] = frame["binary_label"].astype(int) == frame["predicted_label"].astype(int)
    frame["quality_quartile"] = pd.qcut(frame["laplacian_variance"], q=4, labels=["lowest", "low", "high", "highest"], duplicates="drop")
    frame.to_csv(out_dir / "quality_metrics.csv", index=False)
    coverage = _risk_coverage(frame)
    coverage.to_csv(out_dir / "selective_risk_coverage.csv", index=False)
    quality_groups = frame.groupby("quality_quartile", observed=True).agg(
        samples=("image_id", "size"),
        accuracy=("correct", "mean"),
        mean_laplacian_variance=("laplacian_variance", "mean"),
        mean_confidence=("confidence", "mean"),
    ).reset_index()
    quality_groups.to_csv(out_dir / "quality_group_summary.csv", index=False)
    coverage_records = coverage.to_dict(orient="records")
    for record in coverage_records:
        for key, value in list(record.items()):
            if pd.isna(value):
                record[key] = None
    summary = {
        "data_provenance": "genuine",
        "manifest": str(manifest_path.resolve()),
        "predictions": str(predictions_path.resolve()),
        "test_samples": int(len(frame)),
        "analysis_is_post_freeze": True,
        "used_for_model_selection": False,
        "quality_features": ["laplacian_variance", "mean_intensity", "intensity_std", "mean_saturation", "clipped_fraction"],
        "fixed_risk_coverage_points": coverage_records,
        "overall_accuracy": float(frame["correct"].mean()),
        "overall_mean_confidence": float(frame["confidence"].mean()),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    try:
        print(json.dumps(analyze(args.manifest, args.predictions, args.out_dir), indent=2, default=str))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"QUALITY ANALYSIS BLOCKED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
