"""Create a separately versioned HAM10000 development cohort for ISIC task.

HAM10000 is used here only as genuine development data for the new
ISIC-contract task. The old binary checkpoint is never reused. Existing
HAM10000 manifests are read-only inputs. HAM10000 has no patient identifier,
so its existing lesion-level grouping is retained and explicitly recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

LABEL_MAPPING = {"0": "official non-melanoma", "1": "melanoma"}
REQUIRED = {"lesion_id", "image_id", "binary_label", "image_path", "image_sha256", "split"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source(path: Path, expected_split: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")
    if set(frame["split"].astype(str)) != {expected_split}:
        raise ValueError(f"{path} must contain only split={expected_split!r}")
    if frame["image_id"].duplicated().any():
        raise ValueError(f"{path} contains duplicate image IDs")
    if frame["lesion_id"].isna().any() or frame["lesion_id"].astype(str).str.strip().eq("").any():
        raise ValueError(f"{path} contains incomplete lesion IDs")
    labels = pd.to_numeric(frame["binary_label"], errors="coerce")
    if labels.isna().any() or not labels.isin([0, 1]).all():
        raise ValueError(f"{path} contains labels outside 0/1")
    for image_path in frame["image_path"].astype(str):
        if not Path(image_path).is_file():
            raise FileNotFoundError(image_path)
    frame = frame.copy()
    frame["target"] = labels.astype(int)
    return frame


def prepare(
    train_source: Path,
    validation_source: Path,
    test_source: Path,
    review_report: Path,
    isic_external_manifest: Path,
    out_dir: Path,
) -> dict:
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite development directory: {out_dir}")
    train = load_source(train_source, "train")
    validation = load_source(validation_source, "validation")
    test = load_source(test_source, "test")
    review = json.loads(review_report.read_text(encoding="utf-8"))
    if review.get("report_status") != "review_incomplete":
        raise ValueError("Expected the current explicit review report to disclose unresolved candidates")
    unresolved_right_ids = {
        str(item["right_image_id"])
        for item in review.get("unresolved_candidates", [])
        if item.get("disposition") in {"unreviewed", "uncertain"}
    }
    source = pd.concat([train, validation], ignore_index=True)
    if set(source["image_id"]) & set(test["image_id"]):
        raise ValueError("Existing HAM train/validation/test manifests overlap")
    excluded = source.loc[source["image_id"].isin(unresolved_right_ids)].copy()
    excluded["exclusion_reason"] = "unresolved_perceptual_overlap_conservative_exclusion"
    included = source.loc[~source["image_id"].isin(unresolved_right_ids)].copy()
    if set(included.loc[included["split"] == "train", "lesion_id"]) & set(included.loc[included["split"] == "validation", "lesion_id"]):
        raise ValueError("Lesion leakage detected between development train and validation")
    if set(included["lesion_id"]) & set(test["lesion_id"]):
        raise ValueError("Lesion leakage detected between development and preserved HAM test")

    def transform(frame: pd.DataFrame, split: str) -> pd.DataFrame:
        output = frame.copy()
        output["task"] = "isic2020_melanoma_vs_nonmelanoma_v1"
        output["dataset_id"] = "ham10000"
        output["dataset_version"] = "HAM10000 Dataverse version 4"
        output["data_provenance"] = "genuine_ham10000_development"
        output["modality"] = "dermoscopic"
        output["split"] = split
        output["target"] = output["binary_label"].astype(int)
        output["target_label_contract"] = output["target"].map({0: LABEL_MAPPING["0"], 1: LABEL_MAPPING["1"]})
        return output.sort_values("image_id")

    train_out = transform(included.loc[included["split"] == "train"], "train")
    validation_out = transform(included.loc[included["split"] == "validation"], "validation")
    excluded_out = transform(excluded, "development_excluded")
    columns = [
        "task", "dataset_id", "dataset_version", "data_provenance", "modality",
        "split", "lesion_id", "image_id", "dx", "dx_type", "age", "sex",
        "localization", "binary_label", "target", "target_label_contract",
        "image_path", "image_sha256", "binary_category",
    ]
    out_dir.mkdir(parents=True, exist_ok=False)
    train_out[columns].to_csv(out_dir / "train.csv", index=False)
    validation_out[columns].to_csv(out_dir / "validation.csv", index=False)
    excluded_out[columns + ["exclusion_reason"]].to_csv(out_dir / "excluded_development.csv", index=False)
    summary = {
        "task": "isic2020_melanoma_vs_nonmelanoma_v1",
        "status": "ready",
        "development_source": "HAM10000 Dataverse version 4",
        "data_provenance": "genuine_ham10000_development",
        "label_mapping": LABEL_MAPPING,
        "grouping": "lesion_id",
        "patient_id_available": False,
        "train_source": str(train_source.resolve()),
        "train_source_sha256": sha256(train_source),
        "validation_source": str(validation_source.resolve()),
        "validation_source_sha256": sha256(validation_source),
        "preserved_test_source": str(test_source.resolve()),
        "preserved_test_source_sha256": sha256(test_source),
        "review_report": str(review_report.resolve()),
        "review_report_sha256": sha256(review_report),
        "isic_external_manifest": str(isic_external_manifest.resolve()),
        "isic_external_manifest_sha256": sha256(isic_external_manifest),
        "unresolved_overlap_policy": "exclude_HAM10000_members_from_development",
        "unresolved_right_candidate_ids": len(unresolved_right_ids),
        "source_train_rows": int(len(train)),
        "source_validation_rows": int(len(validation)),
        "excluded_overlap_rows": int(len(excluded)),
        "train_rows": int(len(train_out)),
        "validation_rows": int(len(validation_out)),
        "train_patients": None,
        "validation_patients": None,
        "train_lesions": int(train_out["lesion_id"].nunique()),
        "validation_lesions": int(validation_out["lesion_id"].nunique()),
        "train_class_counts": {str(k): int(v) for k, v in train_out["target"].value_counts().sort_index().items()},
        "validation_class_counts": {str(k): int(v) for k, v in validation_out["target"].value_counts().sort_index().items()},
        "preserved_ham_test_used_for_training": False,
        "isic_external_used_for_training": False,
        "old_ham_binary_checkpoint_reused": False,
        "notes": [
            "This is a new task and new development manifest; the existing HAM10000 binary checkpoint is not reused.",
            "HAM10000 does not supply patient identifiers, so lesion-level separation is the strongest available grouping.",
            "The ISIC external manifest remains untouched and is not pooled into development.",
            "Perceptual candidates are not declared duplicates; their HAM members are conservatively withheld from development.",
        ],
    }
    (out_dir / "development_validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-source", type=Path, required=True)
    parser.add_argument("--validation-source", type=Path, required=True)
    parser.add_argument("--test-source", type=Path, required=True)
    parser.add_argument("--review-report", type=Path, required=True)
    parser.add_argument("--isic-external-manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(
            args.train_source,
            args.validation_source,
            args.test_source,
            args.review_report,
            args.isic_external_manifest,
            args.out_dir,
        ), indent=2))
    except (OSError, ValueError, KeyError, FileExistsError) as error:
        print(f"HAM DEVELOPMENT PREPARATION BLOCKED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
