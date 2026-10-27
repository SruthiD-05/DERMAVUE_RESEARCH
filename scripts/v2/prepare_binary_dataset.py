"""Prepare a separately versioned HAM10000 melanoma-vs-other task.

This is intentionally separate from the five-class preparation command. The
negative class means "another original HAM10000 diagnosis", not clinically
benign skin. Original ``dx`` values and metadata are retained in every row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

EXTENSIONS = {".jpg", ".jpeg", ".png"}
REQUIRED = {"image_id", "lesion_id", "dx", "age", "sex", "localization"}
KNOWN_DX = {"nv", "bkl", "df", "vasc", "akiec", "bcc", "mel"}
TASK = "binary_melanoma_other_dx_v1"
LABELS = ["Non-melanoma (other HAM10000 dx)", "Melanoma"]


def _group_column(frame: pd.DataFrame) -> str:
    if "patient_id" in frame.columns and frame["patient_id"].notna().all() and frame["patient_id"].astype(str).str.strip().ne("").all():
        return "patient_id"
    if frame["lesion_id"].notna().all() and frame["lesion_id"].astype(str).str.strip().ne("").all():
        return "lesion_id"
    raise ValueError("A complete patient_id or lesion_id column is required for leakage-safe splitting.")


def _split_groups(frame: pd.DataFrame, group_column: str, seed: int, test_fraction: float, validation_fraction: float):
    inconsistent = frame.groupby(group_column)["binary_label"].nunique()
    if (inconsistent > 1).any():
        bad = inconsistent[inconsistent > 1].index.tolist()
        raise ValueError(f"Groups have inconsistent binary labels: {bad[:10]}")
    groups = frame[[group_column, "binary_label"]].drop_duplicates(group_column)
    train_groups, test_groups = train_test_split(
        groups[group_column].to_numpy(),
        test_size=test_fraction,
        random_state=seed,
        stratify=groups["binary_label"].to_numpy(),
    )
    train_group_frame = groups[groups[group_column].isin(train_groups)]
    train_groups, validation_groups = train_test_split(
        train_group_frame[group_column].to_numpy(),
        test_size=validation_fraction,
        random_state=seed,
        stratify=train_group_frame["binary_label"].to_numpy(),
    )
    split = pd.Series("", index=frame.index, dtype="string")
    split.loc[frame[group_column].isin(train_groups)] = "train"
    split.loc[frame[group_column].isin(validation_groups)] = "validation"
    split.loc[frame[group_column].isin(test_groups)] = "test"
    if (split == "").any():
        raise ValueError("Some rows were not assigned to a split.")
    return split


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare(metadata_csv: Path, image_dirs: list[Path], out_dir: Path, seed: int = 42, test_fraction: float = 0.2, validation_fraction: float = 0.15) -> dict:
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing output directory: {out_dir}")
    frame = pd.read_csv(metadata_csv)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"Metadata is missing required columns: {', '.join(missing)}")
    if frame["image_id"].isna().any() or frame["image_id"].astype(str).str.strip().eq("").any():
        raise ValueError("image_id must be present and non-empty.")
    if frame["dx"].isna().any() or frame["dx"].astype(str).str.strip().eq("").any():
        raise ValueError("dx must be present and non-empty.")
    frame["image_id"] = frame["image_id"].astype(str).str.strip()
    frame["dx"] = frame["dx"].astype(str).str.strip().str.lower()
    if frame["image_id"].duplicated().any():
        raise ValueError("image_id must be present and unique.")
    unknown = sorted(set(frame["dx"]) - KNOWN_DX)
    if unknown:
        raise ValueError(f"Unmapped dx labels found; no binary labels inferred: {unknown}")
    frame["binary_label"] = (frame["dx"] == "mel").astype(int)
    frame["binary_category"] = frame["binary_label"].map({0: LABELS[0], 1: LABELS[1]})

    index: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for directory in image_dirs:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                image_id = path.stem
                if image_id in index:
                    raise ValueError(f"Duplicate image file for image_id={image_id}")
                index[image_id] = path.resolve()
                hashes[image_id] = _sha256(path)
    missing_images = sorted(set(frame["image_id"]) - set(index))
    if missing_images:
        raise ValueError(f"{len(missing_images)} metadata images are missing; first IDs: {missing_images[:5]}")
    frame["image_path"] = frame["image_id"].map(lambda value: str(index[value]))
    frame["image_sha256"] = frame["image_id"].map(hashes)

    duplicate_exclusions: list[str] = []
    for _, group in frame.groupby("image_sha256", sort=False):
        if len(group) < 2:
            continue
        if group["lesion_id"].nunique() != 1 or group["binary_label"].nunique() != 1:
            raise ValueError(f"Exact image content is shared across lesions or binary labels: {group['image_id'].tolist()[:10]}")
        duplicate_exclusions.extend(group.iloc[1:]["image_id"].tolist())
        frame = frame.drop(index=group.index[1:])

    group_column = _group_column(frame)
    frame["split"] = _split_groups(frame, group_column, seed, test_fraction, validation_fraction)
    sets = {name: set(frame.loc[frame["split"] == name, group_column]) for name in ("train", "validation", "test")}
    if sets["train"] & sets["validation"] or sets["train"] & sets["test"] or sets["validation"] & sets["test"]:
        raise ValueError("Group leakage detected between binary splits.")

    out_dir.mkdir(parents=True)
    for name in ("train", "validation", "test"):
        frame.loc[frame["split"] == name].to_csv(out_dir / f"{name}.csv", index=False)
    report = {
        "data_provenance": "genuine-required",
        "task": TASK,
        "metadata_csv": str(metadata_csv.resolve()),
        "image_dirs": [str(path.resolve()) for path in image_dirs],
        "label_mapping": {"0": LABELS[0], "1": LABELS[1]},
        "positive_dx": ["mel"],
        "negative_dx": sorted(KNOWN_DX - {"mel"}),
        "negative_class_limitation": "Other original HAM10000 diagnoses, not a claim of benign or low clinical risk.",
        "group_column": group_column,
        "seed": seed,
        "test_fraction": test_fraction,
        "validation_fraction_of_train": validation_fraction,
        "rows": int(len(frame)),
        "original_dx_distribution": frame["dx"].value_counts().sort_index().to_dict(),
        "binary_distribution": frame["binary_category"].value_counts().to_dict(),
        "split_distribution": {
            f"{split_name}:{category}": int(count)
            for (split_name, category), count in frame.groupby(["split", "binary_category"]).size().items()
        },
        "exact_duplicate_exclusions_same_lesion": duplicate_exclusions,
        "test_is_separate_task_projection": True,
        "five_class_test_artifacts_modified": False,
    }
    (out_dir / "dataset_validation.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (out_dir / "label_mapping.json").write_text(json.dumps(report["label_mapping"], indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata_csv", type=Path, required=True)
    parser.add_argument("--images_dir", type=Path, action="append", required=True)
    parser.add_argument("--out_dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test_fraction", type=float, default=0.2)
    parser.add_argument("--validation_fraction", type=float, default=0.15)
    args = parser.parse_args()
    try:
        report = prepare(args.metadata_csv, args.images_dir, args.out_dir, args.seed, args.test_fraction, args.validation_fraction)
    except (OSError, ValueError, KeyError) as error:
        print(f"BINARY DATASET VALIDATION FAILED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
