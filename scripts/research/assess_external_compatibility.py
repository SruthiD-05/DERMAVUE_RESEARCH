"""Compare a frozen external manifest with a saved V2 experiment bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assess(manifest_path: Path, bundle: Path, out: Path) -> dict:
    manifest = pd.read_csv(manifest_path)
    required_files = [
        "cnn_branch.keras", "fusion_classifier.joblib", "fusion_scaler.joblib",
        "metadata_pipeline.joblib", "feature_names.json", "label_mapping.json",
        "training_config.json", "artifact_manifest.json",
    ]
    missing_files = [name for name in required_files if not (bundle / name).is_file()]
    config = json.loads((bundle / "training_config.json").read_text(encoding="utf-8")) if (bundle / "training_config.json").is_file() else {}
    labels = json.loads((bundle / "label_mapping.json").read_text(encoding="utf-8")) if (bundle / "label_mapping.json").is_file() else {}
    features = json.loads((bundle / "feature_names.json").read_text(encoding="utf-8")) if (bundle / "feature_names.json").is_file() else {}
    required_metadata = {"age", "sex", "localization"}
    missing_metadata = sorted(required_metadata - set(manifest.columns))
    external_labels = {
        "0": "Non-melanoma (official ISIC 2020 target)",
        "1": "Melanoma (official ISIC 2020 target)",
    }
    label_contract_compatible = labels == {"0": "Non-melanoma (official ISIC 2020 target)", "1": "Melanoma"}
    result = {
        "evaluation_allowed": bool(not missing_files and not missing_metadata and label_contract_compatible),
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": sha256(manifest_path),
        "bundle": str(bundle.resolve()),
        "bundle_artifact_manifest_sha256": sha256(bundle / "artifact_manifest.json") if (bundle / "artifact_manifest.json").is_file() else None,
        "checkpoint_files_present": not missing_files,
        "missing_checkpoint_files": missing_files,
        "external_modality": str(manifest["modality"].iloc[0]) if "modality" in manifest and len(manifest) else None,
        "bundle_image_size": config.get("image", {}).get("size"),
        "bundle_metadata_features": features.get("metadata_features", []),
        "external_required_metadata_missing": missing_metadata,
        "external_label_contract": external_labels,
        "bundle_label_contract": labels,
        "label_contract_compatible": label_contract_compatible,
        "localization_vocabularies_require_review": True,
        "missing_modality_behavior": "not applicable: external candidate is dermoscopic-only and supplies no verified clinical pairing",
        "reason_blocked": "The existing binary checkpoint was trained with non-melanoma=other HAM10000 dx, while ISIC 2020 target=0 means official non-melanoma; this is a label-contract mismatch. No external scoring is permitted until a separately versioned compatible experiment is approved.",
        "evaluated": False,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(assess(args.manifest, args.bundle, args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
