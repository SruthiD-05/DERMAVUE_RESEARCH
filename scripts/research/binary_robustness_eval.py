"""Post-freeze robustness evaluation under fixed image corruptions.

This script does not train, calibrate, select thresholds, or alter any
artifact. Corruption definitions and severities are fixed before scoring.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score,
                             brier_score_loss, confusion_matrix,
                             recall_score, roc_auc_score)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "model" / "v2_source" / "src"
sys.path.insert(0, str(SOURCE))

from handcrafted_features import extract_handcrafted_features  # noqa: E402
from preprocessing import preprocess_image  # noqa: E402
from segmentation import segment_lesion  # noqa: E402
from cnn_model import extract_deep_features, get_feature_extractor  # noqa: E402


def _metrics(labels, probabilities, threshold=0.5) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "melanoma_sensitivity": float(recall_score(labels, predictions, zero_division=0)),
        "melanoma_specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "auroc": float(roc_auc_score(labels, probabilities)),
        "auprc": float(average_precision_score(labels, probabilities)),
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "false_negatives": int(fn),
        "false_positives": int(fp),
        "test_samples": int(len(labels)),
    }


def _corrupt(image: np.ndarray, kind: str, index: int, seed: int) -> np.ndarray:
    if kind == "gaussian_blur_k9":
        return cv2.GaussianBlur(image, (9, 9), 0)
    if kind == "gaussian_noise_sigma20":
        rng = np.random.default_rng(seed + index)
        noise = rng.normal(0.0, 20.0, image.shape)
        return np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    if kind == "brightness_dark_0.65":
        return np.clip(image.astype(np.float32) * 0.65, 0, 255).astype(np.uint8)
    if kind == "jpeg_quality30":
        success, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
        if not success:
            raise ValueError("JPEG corruption encoding failed")
        decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if decoded is None:
            raise ValueError("JPEG corruption decoding failed")
        return decoded
    raise ValueError(f"Unknown corruption: {kind}")


def _predict_images(model, classifier, scaler, metadata, frame: pd.DataFrame, images: list[np.ndarray], img_size: int) -> np.ndarray:
    processed = [preprocess_image(image, size=img_size) for image in images]
    masks = [segment_lesion(image)[0] for image in processed]
    deep = extract_deep_features(get_feature_extractor(model), np.asarray(processed, dtype=np.uint8))
    handcrafted = np.asarray([extract_handcrafted_features(image, mask) for image, mask in zip(processed, masks)], dtype=np.float32)
    metadata_features = metadata.transform(frame[["age", "sex", "localization"]])
    if hasattr(metadata_features, "toarray"):
        metadata_features = metadata_features.toarray()
    fused = np.concatenate([deep, handcrafted, np.asarray(metadata_features, dtype=np.float32)], axis=1)
    probabilities = classifier.predict_proba(scaler.transform(fused))[:, 1]
    return probabilities


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        import tensorflow as tf

        frame = pd.read_csv(args.manifest).sort_values("image_id").reset_index(drop=True)
        if set(frame["split"]) != {"test"}:
            raise ValueError("Robustness evaluation requires a test-only manifest.")
        labels = frame["binary_label"].astype(int).to_numpy()
        config = json.loads((args.bundle / "training_config.json").read_text(encoding="utf-8"))
        threshold = float(config["selected_threshold"])
        model = tf.keras.models.load_model(args.bundle / "cnn_branch.keras")
        classifier = joblib.load(args.bundle / "fusion_classifier.joblib")
        scaler = joblib.load(args.bundle / "fusion_scaler.joblib")
        metadata = joblib.load(args.bundle / "metadata_pipeline.joblib")
        original_images = [cv2.imread(path) for path in frame["image_path"]]
        if any(image is None for image in original_images):
            raise ValueError("At least one test image could not be decoded.")
        corruption_names = ["gaussian_blur_k9", "gaussian_noise_sigma20", "brightness_dark_0.65", "jpeg_quality30"]
        rows = []
        args.out_dir.mkdir(parents=True, exist_ok=True)
        for name in corruption_names:
            corrupted = [_corrupt(image, name, index, args.seed) for index, image in enumerate(original_images)]
            probabilities = _predict_images(model, classifier, scaler, metadata, frame, corrupted, int(config.get("image", {}).get("size", 128)))
            result = {"condition": name, "threshold": threshold, **_metrics(labels, probabilities, threshold), "data_provenance": "genuine", "post_freeze_only": True}
            rows.append(result)
            output = frame[["image_id", "lesion_id", "binary_label"]].copy()
            output["probability_melanoma"] = probabilities
            output["predicted_label"] = (probabilities >= threshold).astype(int)
            output.to_csv(args.out_dir / f"predictions_{name}.csv", index=False)
        metrics = pd.DataFrame(rows)
        metrics.to_csv(args.out_dir / "corruption_metrics.csv", index=False)
        (args.out_dir / "protocol.json").write_text(json.dumps({
            "manifest": str(args.manifest.resolve()),
            "bundle": str(args.bundle.resolve()),
            "corruptions": corruption_names,
            "threshold": threshold,
            "seed": args.seed,
            "test_used_for_selection": False,
            "notes": "Moderate fixed corruptions are exploratory post-freeze analyses, not clinical safety tests.",
        }, indent=2), encoding="utf-8")
        print(metrics.to_json(orient="records", indent=2))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"ROBUSTNESS EVALUATION BLOCKED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
