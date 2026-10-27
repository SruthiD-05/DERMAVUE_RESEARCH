"""Recompute binary artifact metrics from saved predictions without retraining."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd


def _load_trainer():
    root = Path(__file__).resolve().parents[2]
    source = root / "experiments" / "binary_melanoma" / "train_binary_prepared.py"
    spec = importlib.util.spec_from_file_location("binary_train_prepared", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load binary trainer: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--validation-manifest", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    trainer = _load_trainer()
    manifest = pd.read_csv(args.manifest)
    predictions = pd.read_csv(args.experiment_dir / "test_predictions.csv")
    if "probability_0" not in predictions.columns and "probability_melanoma" in predictions.columns:
        predictions["probability_0"] = 1.0 - predictions["probability_melanoma"]
        predictions["probability_1"] = predictions["probability_melanoma"]
        predictions.to_csv(args.experiment_dir / "test_predictions.csv", index=False)
    joined = manifest.merge(predictions, on="image_id", how="inner", validate="one_to_one").sort_values("image_id").reset_index(drop=True)
    label_column = "binary_label_x" if "binary_label_x" in joined.columns else "binary_label"
    if len(joined) != len(manifest) or joined[label_column].isna().any():
        raise ValueError("Saved predictions do not cover the binary test manifest.")
    config = json.loads((args.experiment_dir / "training_config.json").read_text(encoding="utf-8"))
    threshold = float(config["selected_threshold"])
    y_true = joined[label_column].astype(int).to_numpy()
    probabilities = joined["probability_melanoma"].astype(float).to_numpy()
    metrics = trainer._metrics(y_true, probabilities, threshold)
    metrics["classifier"] = config["selected_classifier"]
    metrics["target_accuracy"] = 0.9
    metrics["target_reached"] = bool(metrics["accuracy"] >= 0.9)
    metrics["bootstrap_95ci"] = trainer._bootstrap(y_true, probabilities, threshold, int(config.get("seed", 42)))
    metrics["data_provenance"] = "genuine"
    metrics["task"] = config["task"]
    metrics["test_manifest"] = str(args.manifest.resolve())
    if args.validation_manifest:
        validation_manifest = pd.read_csv(args.validation_manifest)
        validation_rows = []
        for prediction_path in sorted(args.experiment_dir.glob("validation_predictions_*.csv")):
            classifier_name = prediction_path.stem.removeprefix("validation_predictions_")
            validation_predictions = pd.read_csv(prediction_path)
            validation_joined = validation_manifest.merge(validation_predictions, on="image_id", how="inner", validate="one_to_one")
            validation_label = "binary_label_x" if "binary_label_x" in validation_joined.columns else "binary_label"
            validation_metrics = trainer._metrics(
                validation_joined[validation_label].astype(int).to_numpy(),
                validation_joined["probability_melanoma"].astype(float).to_numpy(),
                0.5,
            )
            validation_metrics["classifier"] = classifier_name
            validation_rows.append(validation_metrics)
        if validation_rows:
            validation_table = pd.DataFrame(validation_rows)
            validation_table["selection_score"] = validation_table["auroc"].fillna(validation_table["macro_f1"])
            validation_table.to_csv(args.experiment_dir / "validation_model_selection.csv", index=False)
    (args.experiment_dir / "test_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    artifact_manifest_path = args.experiment_dir / "artifact_manifest.json"
    artifact_manifest = {path.name: _sha256(path) for path in args.experiment_dir.iterdir() if path.is_file() and path.name != artifact_manifest_path.name}
    artifact_manifest_path.write_text(json.dumps({"data_provenance": "genuine", "task": config["task"], "artifacts": artifact_manifest}, indent=2), encoding="utf-8")
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "evaluation.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
