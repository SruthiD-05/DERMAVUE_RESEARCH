"""Generate probabilities for the frozen ISIC 2020 external manifest.

This command is intentionally separate from training and does not read
external labels. It requires a checkpoint produced by the versioned ISIC task
and records the checkpoint/configuration hashes in a sidecar JSON file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import pandas as pd

LABEL_MAPPING = {"0": "official non-melanoma", "1": "melanoma"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_completed_overlap_review(review_path: Path) -> dict:
    if not review_path.is_file():
        raise FileNotFoundError(review_path)
    report = json.loads(review_path.read_text(encoding="utf-8"))
    counts = report.get("disposition_counts", {})
    if report.get("report_status") not in {"complete", "review_complete"}:
        raise ValueError("External prediction blocked until the HAM/ISIC overlap review is complete")
    if int(counts.get("unreviewed", 0)) or int(counts.get("uncertain", 0)):
        raise ValueError("External prediction blocked while overlap candidates remain unreviewed or uncertain")
    return report


def predict(manifest_path: Path, checkpoint: Path, config_path: Path, out: Path, overlap_review_report: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite prediction file: {out}")
    manifest = pd.read_csv(manifest_path)
    required = {"image_id", "image_path", "data_provenance", "split"}
    missing = sorted(required - set(manifest.columns))
    if missing:
        raise ValueError(f"External manifest is missing columns: {missing}")
    if set(manifest["data_provenance"].astype(str)) != {"genuine_external"}:
        raise ValueError("Prediction input is not genuine_external")
    if set(manifest["split"].astype(str)) != {"external_evaluation"}:
        raise ValueError("Prediction input is not external_evaluation")
    review_report = _require_completed_overlap_review(overlap_review_report)
    if manifest["image_id"].duplicated().any():
        raise ValueError("Prediction input contains duplicate image IDs")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("task") != "isic2020_melanoma_vs_nonmelanoma_v1" or config.get("label_mapping") != LABEL_MAPPING:
        raise ValueError("Checkpoint configuration does not declare the official ISIC task contract")
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    try:
        import tensorflow as tf
    except ImportError as error:
        raise RuntimeError("TensorFlow is required; no predictions were generated") from error
    size = int(config["preprocessing"]["image_size"])
    bundle_config_path = checkpoint.parent / "training_config.json"
    if not bundle_config_path.is_file():
        raise ValueError("Checkpoint bundle is missing training_config.json")
    bundle_config = json.loads(bundle_config_path.read_text(encoding="utf-8"))
    if bundle_config.get("task") != config["task"] or bundle_config.get("label_mapping") != LABEL_MAPPING:
        raise ValueError("Checkpoint bundle task or label mapping is incompatible")
    if int(bundle_config.get("preprocessing", {}).get("image_size", -1)) != size:
        raise ValueError("Checkpoint bundle preprocessing size is incompatible")
    model = tf.keras.models.load_model(checkpoint)
    if tuple(model.input_shape[1:]) != (size, size, 3) or int(model.output_shape[-1]) != 1:
        raise ValueError("Checkpoint architecture shape is incompatible with the binary task")
    activation = getattr(model.layers[-1], "activation", None)
    if activation is None or getattr(activation, "__name__", "") != "sigmoid":
        raise ValueError("Checkpoint output must be a single sigmoid melanoma probability")
    paths = manifest["image_path"].astype(str).to_numpy()
    for image_path in paths:
        if not Path(image_path).is_file():
            raise FileNotFoundError(image_path)

    def load(path):
        image = tf.io.decode_jpeg(tf.io.read_file(path), channels=3)
        image = tf.image.resize(image, [size, size], antialias=True)
        image = tf.cast(image, tf.float32)
        return tf.keras.applications.mobilenet_v2.preprocess_input(image)

    dataset = tf.data.Dataset.from_tensor_slices(paths).map(load, num_parallel_calls=1)
    dataset = dataset.batch(int(config["training"]["batch_size"])).prefetch(1)
    probabilities = model.predict(dataset, verbose=0).reshape(-1)
    if len(probabilities) != len(manifest):
        raise ValueError("Checkpoint did not produce one probability per image")
    output = pd.DataFrame({
        "image_id": manifest["image_id"].astype(str),
        "probability_0": 1.0 - probabilities,
        "probability_1": probabilities,
    })
    out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(out, index=False)
    sidecar = {
        "task": config["task"],
        "label_mapping": LABEL_MAPPING,
        "data_provenance": "genuine_external_predictions",
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": sha256(manifest_path),
        "checkpoint": str(checkpoint.resolve()),
        "checkpoint_sha256": sha256(checkpoint),
        "config": str(config_path.resolve()),
        "config_sha256": sha256(config_path),
        "checkpoint_bundle_config": str(bundle_config_path.resolve()),
        "checkpoint_bundle_config_sha256": sha256(bundle_config_path),
        "prediction_file": str(out.resolve()),
        "prediction_sha256": sha256(out),
        "rows": len(output),
        "software": {"python": platform.python_version(), "tensorflow": tf.__version__},
        "external_labels_used_for_prediction": False,
        "overlap_review_report": str(overlap_review_report.resolve()),
        "overlap_review_report_sha256": sha256(overlap_review_report),
        "overlap_review_status": review_report["report_status"],
    }
    sidecar_path = out.with_suffix(out.suffix + ".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return sidecar


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--overlap-review-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(predict(args.manifest, args.checkpoint, args.config, args.out, args.overlap_review_report), indent=2))
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"ISIC PREDICTION BLOCKED: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
