"""Validate and freeze the public ISIC 2020 external-evaluation manifest.

This preparation step never trains a model and never creates labels.  It uses
the official ISIC 2020 ground-truth file, excludes the source-published
duplicate pairs conservatively, excludes rows whose diagnosis is ``unknown``
from the primary binary endpoint, and requires a complete patient identifier
for patient-grouped external evaluation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REQUIRED = {
    "image_name",
    "patient_id",
    "sex",
    "age_approx",
    "anatom_site_general_challenge",
    "diagnosis",
    "benign_malignant",
    "target",
}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_hash(path: Path) -> str:
    return _sha256(path)


def _load_duplicate_ids(path: Path) -> tuple[set[str], int]:
    frame = pd.read_csv(path)
    required = {"image_name_1", "image_name_2"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Official duplicate file is missing columns: {missing}")
    ids = set(frame["image_name_1"].dropna().astype(str)) | set(frame["image_name_2"].dropna().astype(str))
    return ids, int(len(frame))


def prepare(metadata_csv: Path, duplicate_csv: Path, images_dir: Path, out_dir: Path) -> dict:
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing external manifest directory: {out_dir}")
    if not metadata_csv.is_file() or not duplicate_csv.is_file() or not images_dir.is_dir():
        raise ValueError("metadata, duplicate list, and image directory must all exist")

    metadata = pd.read_csv(metadata_csv)
    missing = sorted(REQUIRED - set(metadata.columns))
    if missing:
        raise ValueError(f"ISIC 2020 ground truth is missing required columns: {missing}")
    if metadata["image_name"].isna().any():
        raise ValueError("image_name must not contain missing values")
    metadata["image_name"] = metadata["image_name"].astype(str).str.strip()
    if metadata["image_name"].eq("").any() or metadata["image_name"].duplicated().any():
        raise ValueError("image_name must be non-empty and unique")
    if metadata["patient_id"].isna().any() or metadata["patient_id"].astype(str).str.strip().eq("").any():
        raise ValueError("patient_id must be complete for patient-grouped evaluation")
    target = pd.to_numeric(metadata["target"], errors="coerce")
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError("ISIC 2020 target must contain only official binary 0/1 labels")
    metadata["target"] = target.astype(int)

    image_index: dict[str, Path] = {}
    for path in sorted(images_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        image_id = path.stem
        if image_id in image_index:
            raise ValueError(f"Multiple image files found for image_name={image_id}")
        image_index[image_id] = path.resolve()
    missing_images = sorted(set(metadata["image_name"]) - set(image_index))
    extra_images = sorted(set(image_index) - set(metadata["image_name"]))
    if missing_images:
        raise ValueError(f"{len(missing_images)} metadata rows have no image file; first IDs: {missing_images[:10]}")

    duplicate_ids, duplicate_pairs = _load_duplicate_ids(duplicate_csv)
    frame = metadata.copy()
    frame["image_path"] = frame["image_name"].map(lambda value: str(image_index[value]))
    frame["image_sha256"] = frame["image_path"].map(lambda value: _file_hash(Path(value)))
    frame["external_binary_label"] = frame["target"]
    frame["image_id"] = frame["image_name"]
    frame["lesion_id"] = pd.NA
    frame["age"] = pd.to_numeric(frame["age_approx"], errors="coerce")
    frame["localization"] = frame["anatom_site_general_challenge"]
    frame["task"] = "isic2020_binary_melanoma_v1"
    frame["dataset_id"] = "isic2020"
    frame["dataset_version"] = "ISIC 2020 Challenge Dataset"
    frame["modality"] = "dermoscopic"
    frame["split"] = "external_evaluation"
    frame["data_provenance"] = "genuine_external"

    reasons: dict[str, list[str]] = {}
    for image_id in frame.loc[frame["image_name"].isin(duplicate_ids), "image_name"]:
        reasons.setdefault(image_id, []).append("official_duplicate_pair")
    unknown_mask = frame["diagnosis"].astype(str).str.strip().str.lower().eq("unknown")
    for image_id in frame.loc[unknown_mask, "image_name"]:
        reasons.setdefault(image_id, []).append("unknown_diagnosis_primary_exclusion")

    # Exclude every member of an exact-content duplicate group from the
    # primary endpoint.  This is conservative for an external evaluation.
    duplicate_groups = frame.groupby("image_sha256")["image_name"].agg(list)
    exact_duplicate_ids: set[str] = set()
    for ids in duplicate_groups:
        if len(ids) > 1:
            exact_duplicate_ids.update(ids)
            for image_id in ids:
                reasons.setdefault(image_id, []).append("exact_duplicate_content")

    excluded_ids = set(reasons)
    primary = frame.loc[~frame["image_name"].isin(excluded_ids)].copy()
    if primary.empty:
        raise ValueError("No rows remain for the primary external evaluation manifest")
    if primary["patient_id"].duplicated().any():
        # This is expected and useful: bootstrap must sample patients, not
        # images.  It is recorded rather than treated as an error.
        patient_grouping = "patient_id"
    else:
        patient_grouping = "patient_id"

    excluded = frame.loc[frame["image_name"].isin(excluded_ids)].copy()
    excluded["exclusion_reason"] = excluded["image_name"].map(lambda value: ";".join(reasons[value]))
    columns = [
        "dataset_id", "dataset_version", "task", "split", "data_provenance",
        "image_id", "image_name", "image_path", "image_sha256", "patient_id",
        "lesion_id", "sex", "age", "localization", "diagnosis",
        "benign_malignant", "target", "external_binary_label", "modality",
    ]
    out_dir.mkdir(parents=True, exist_ok=False)
    frame[columns].sort_values("image_id").to_csv(out_dir / "all_rows.csv", index=False)
    primary[columns].sort_values("image_id").to_csv(out_dir / "external_evaluation.csv", index=False)
    excluded[columns + ["exclusion_reason"]].sort_values("image_id").to_csv(out_dir / "excluded_rows.csv", index=False)
    report = {
        "data_provenance": "genuine_external",
        "dataset_id": "isic2020",
        "dataset_version": "ISIC 2020 Challenge Dataset",
        "source_urls": [
            "https://challenge.isic-archive.com/data/",
            "https://isic-archive.s3.amazonaws.com/challenges/2020/ISIC_2020_Training_JPEG.zip",
        ],
        "metadata_sha256": _file_hash(metadata_csv),
        "duplicate_list_sha256": _file_hash(duplicate_csv),
        "images_dir": str(images_dir.resolve()),
        "image_count_in_official_ground_truth": int(len(frame)),
        "image_count_found": int(len(image_index)),
        "extra_image_count": int(len(extra_images)),
        "official_duplicate_pair_count": duplicate_pairs,
        "official_duplicate_image_count": int(len(duplicate_ids)),
        "exact_duplicate_content_image_count": int(len(exact_duplicate_ids)),
        "unknown_diagnosis_count": int(unknown_mask.sum()),
        "excluded_row_count": int(len(excluded)),
        "primary_external_evaluation_rows": int(len(primary)),
        "patient_count_primary": int(primary["patient_id"].nunique()),
        "patient_grouping": patient_grouping,
        "lesion_id_available": False,
        "skin_tone_label_available": False,
        "paired_clinical_modality_available": False,
        "label_mapping": {
            "external_binary_label": "official ISIC 2020 target: 1=melanoma, 0=non-melanoma",
            "primary_exclusion": "diagnosis=unknown, official duplicate pairs, or exact duplicate image content",
        },
        "notes": [
            "This is an evaluation-only manifest; no rows may be used for training, calibration, threshold selection, or model selection.",
            "The release provides patient_id but not lesion_id; patient-level grouped uncertainty is supported, lesion-level independence is not established.",
            "The existing binary_melanoma_other_dx_v1 checkpoint has a different negative-label contract and is not silently evaluated against this manifest.",
        ],
    }
    (out_dir / "dataset_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-csv", type=Path, required=True)
    parser.add_argument("--duplicate-csv", type=Path, required=True)
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = prepare(args.metadata_csv, args.duplicate_csv, args.images_dir, args.out_dir)
    except (OSError, ValueError, KeyError, FileExistsError) as error:
        print(f"EXTERNAL DATASET VALIDATION FAILED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
