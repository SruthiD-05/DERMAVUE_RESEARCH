"""Validate genuine V2 data and create deterministic group-safe manifests.

This script is intentionally preparation-only. It never creates images or
labels and never trains a model. It uses the label mapping from the preserved
V2 real-data source and fails closed on invalid or ambiguous inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

SOURCE = Path(__file__).resolve().parents[2] / "backend" / "model" / "v2_source" / "src"
sys.path.insert(0, str(SOURCE))
from metadata_features import DX_TO_CATEGORY, LABEL_TO_IDX, RISK_CATEGORIES  # noqa: E402

REQUIRED = {"image_id", "lesion_id", "dx", "age", "sex", "localization"}
EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _group_column(frame: pd.DataFrame) -> str:
    if "patient_id" in frame.columns and frame["patient_id"].notna().all() and frame["patient_id"].astype(str).str.strip().ne("").all():
        return "patient_id"
    if frame["lesion_id"].notna().all() and frame["lesion_id"].astype(str).str.strip().ne("").all():
        return "lesion_id"
    raise ValueError("A complete patient_id or lesion_id column is required for leakage-safe splitting.")


def _split_groups(frame: pd.DataFrame, group_column: str, seed: int, test_fraction: float, val_fraction: float):
    inconsistent = frame.groupby(group_column)["risk_label"].nunique()
    if (inconsistent > 1).any():
        bad = inconsistent[inconsistent > 1].index.tolist()
        raise ValueError(f"Groups have inconsistent labels: {bad[:10]}")
    groups = frame[[group_column, "risk_label"]].drop_duplicates(group_column)
    train_groups, test_groups = train_test_split(
        groups[group_column].to_numpy(), test_size=test_fraction, random_state=seed,
        stratify=groups["risk_label"].to_numpy(),
    )
    train_group_frame = groups[groups[group_column].isin(train_groups)]
    train_groups, val_groups = train_test_split(
        train_group_frame[group_column].to_numpy(), test_size=val_fraction,
        random_state=seed, stratify=train_group_frame["risk_label"].to_numpy(),
    )
    split = pd.Series("", index=frame.index, dtype="string")
    split.loc[frame[group_column].isin(train_groups)] = "train"
    split.loc[frame[group_column].isin(val_groups)] = "validation"
    split.loc[frame[group_column].isin(test_groups)] = "test"
    if (split == "").any():
        raise ValueError("Some rows were not assigned to a split.")
    return split


def validate_and_prepare(metadata_csv: Path, image_dirs: list[Path], out_dir: Path, seed: int = 42, test_fraction: float = 0.2, val_fraction: float = 0.15, task: str = "ham10000_five_class"):
    if task != "ham10000_five_class":
        raise ValueError("Only ham10000_five_class is implemented by this metadata preparation command; use a separately documented binary mapping and pipeline rather than silently collapsing labels.")
    frame = pd.read_csv(metadata_csv)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"Metadata is missing required columns: {', '.join(missing)}")
    if frame["image_id"].isna().any() or frame["image_id"].duplicated().any():
        raise ValueError("image_id must be present and unique.")
    frame["image_id"] = frame["image_id"].astype(str).str.strip()
    frame["risk_category"] = frame["dx"].map(DX_TO_CATEGORY)
    if frame["risk_category"].isna().any():
        raise ValueError("Metadata contains unmapped dx labels; no labels were inferred.")
    frame["risk_label"] = frame["risk_category"].map(LABEL_TO_IDX).astype(int)

    index: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for directory in image_dirs:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                image_id = path.stem
                if image_id in index:
                    raise ValueError(f"Duplicate image file for image_id={image_id}")
                index[image_id] = path.resolve()
                hashes[image_id] = hashlib.sha256(path.read_bytes()).hexdigest()
    missing_images = sorted(set(frame["image_id"]) - set(index))
    if missing_images:
        raise ValueError(f"{len(missing_images)} metadata images are missing; first IDs: {missing_images[:5]}")
    frame["image_path"] = frame["image_id"].map(lambda value: str(index[value]))
    frame["image_sha256"] = frame["image_id"].map(hashes)
    duplicate_exclusions = []
    for digest, group in frame.groupby("image_sha256", sort=False):
        if len(group) < 2:
            continue
        if group["lesion_id"].nunique() != 1 or group["risk_label"].nunique() != 1:
            duplicates = group["image_id"].tolist()
            raise ValueError(f"Exact image content is shared across lesions or labels: {duplicates[:10]}")
        keep = group.index[0]
        excluded = group.index[1:]
        duplicate_exclusions.extend(frame.loc[excluded, "image_id"].tolist())
        frame = frame.drop(index=excluded)

    group_column = _group_column(frame)
    frame["split"] = _split_groups(frame, group_column, seed, test_fraction, val_fraction)
    sets = {name: set(frame.loc[frame["split"] == name, group_column]) for name in ("train", "validation", "test")}
    if sets["train"] & sets["validation"] or sets["train"] & sets["test"] or sets["validation"] & sets["test"]:
        raise ValueError("Group leakage detected between splits.")

    out_dir.mkdir(parents=True, exist_ok=False)
    for name in ("train", "validation", "test"):
        frame.loc[frame["split"] == name].to_csv(out_dir / f"{name}.csv", index=False)
    report = {
        "data_provenance": "genuine-required",
        "metadata_csv": str(metadata_csv.resolve()),
        "image_dirs": [str(path.resolve()) for path in image_dirs],
        "task": "ham10000_five_class",
        "labels": RISK_CATEGORIES,
        "group_column": group_column,
        "seed": seed,
        "test_fraction": test_fraction,
        "validation_fraction_of_train": val_fraction,
        "rows": int(len(frame)),
        "class_distribution": frame["risk_category"].value_counts().to_dict(),
        "split_distribution": {
            f"{split_name}:{risk_category}": int(count)
            for (split_name, risk_category), count in frame.groupby(["split", "risk_category"]).size().items()
        },
        "exact_duplicate_exclusions_same_lesion": duplicate_exclusions,
    }
    (out_dir / "dataset_validation.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata_csv", type=Path, required=True)
    parser.add_argument("--images_dir", type=Path, action="append", required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test_fraction", type=float, default=0.2)
    parser.add_argument("--validation_fraction", type=float, default=0.15)
    parser.add_argument("--task", choices=["ham10000_five_class"], default="ham10000_five_class")
    args = parser.parse_args()
    try:
        report = validate_and_prepare(args.metadata_csv, args.images_dir, args.out_dir, args.seed, args.test_fraction, args.validation_fraction, args.task)
    except (OSError, ValueError, KeyError) as error:
        print(f"DATASET VALIDATION FAILED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
