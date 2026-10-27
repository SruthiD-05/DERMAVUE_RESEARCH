"""Prepare a leakage-safe ISIC 2020 development cohort without training.

The frozen external manifest is an immutable evaluation artifact. This script
never edits it and refuses to treat its rows as development data. It records
every source row as included or excluded, applies a conservative policy to
unresolved perceptual candidates, and writes train/validation manifests only
when a genuine labeled development cohort remains.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

LABELS = {"0": "official non-melanoma", "1": "melanoma"}
REQUIRED = {"image_id", "image_path", "patient_id", "diagnosis", "target", "image_sha256"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_csv(path: Path, name: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")
    if frame["image_id"].duplicated().any():
        raise ValueError(f"{name} contains duplicate image IDs")
    if frame["patient_id"].isna().any() or frame["patient_id"].astype(str).str.strip().eq("").any():
        raise ValueError(f"{name} contains incomplete patient IDs")
    target = pd.to_numeric(frame["target"], errors="coerce")
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError(f"{name} contains labels outside the official 0/1 contract")
    frame = frame.copy()
    frame["target"] = target.astype(int)
    return frame


def _review_left_ids(review_report: dict, disposition_names: set[str]) -> set[str]:
    ids = set()
    for item in review_report.get("unresolved_candidates", []):
        if item.get("disposition") in disposition_names:
            ids.add(str(item["left_image_id"]))
    for item in review_report.get("confirmed_duplicates", []):
        if "confirmed_duplicate" in disposition_names:
            ids.add(str(item["left_image_id"]))
    return ids


def prepare(
    all_manifest: Path,
    external_manifest: Path,
    excluded_manifest: Path,
    review_report: Path,
    out_dir: Path,
    seed: int = 42,
    validation_fraction: float = 0.2,
    unresolved_policy: str = "exclude",
) -> dict:
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite task directory: {out_dir}")
    if unresolved_policy not in {"exclude", "retain_with_disclosure"}:
        raise ValueError("unresolved_policy must be exclude or retain_with_disclosure")
    all_rows = _load_csv(all_manifest, "all_rows")
    external = _load_csv(external_manifest, "external_evaluation")
    excluded = pd.read_csv(excluded_manifest)
    if "image_id" not in excluded or "exclusion_reason" not in excluded:
        raise ValueError("excluded_rows must contain image_id and exclusion_reason")
    review = json.loads(review_report.read_text(encoding="utf-8"))
    if review.get("report_status") != "complete" and unresolved_policy == "retain_with_disclosure":
        raise ValueError("retain_with_disclosure requires a completed review report")

    source_ids = set(all_rows["image_id"].astype(str))
    external_ids = set(external["image_id"].astype(str))
    excluded_ids = set(excluded["image_id"].astype(str))
    unresolved_ids = _review_left_ids(review, {"uncertain", "unreviewed"})
    confirmed_ids = _review_left_ids(review, {"confirmed_duplicate"})
    reasons: dict[str, list[str]] = {str(image_id): [] for image_id in all_rows["image_id"]}

    if not external_ids.issubset(source_ids):
        raise ValueError("Frozen external manifest contains IDs absent from all_rows")
    for image_id in external_ids:
        reasons[image_id].append("frozen_external_evaluation")
    for image_id in excluded_ids:
        if image_id in reasons:
            reasons[image_id].append("official_or_exact_duplicate_exclusion")
    for image_id in all_rows.loc[all_rows["diagnosis"].astype(str).str.lower().eq("unknown"), "image_id"]:
        reasons[str(image_id)].append("unknown_diagnosis_no_supervised_label")
    for image_id in confirmed_ids:
        if image_id in reasons:
            reasons[image_id].append("confirmed_cross_dataset_overlap")
    if unresolved_policy == "exclude":
        for image_id in unresolved_ids:
            if image_id in reasons:
                reasons[image_id].append("unresolved_perceptual_overlap_conservative_exclusion")

    included_mask = all_rows["image_id"].map(lambda value: not reasons[str(value)])
    included = all_rows.loc[included_mask].copy()
    excluded_rows = all_rows.loc[~included_mask].copy()
    excluded_rows["exclusion_reason"] = excluded_rows["image_id"].map(lambda value: ";".join(reasons[str(value)]))
    if not included.empty:
        included["task"] = "isic2020_melanoma_vs_nonmelanoma_v1"
        included["data_provenance"] = "genuine_isic_development"
        included["modality"] = included.get("modality", "dermoscopic")
        groups = included["patient_id"].astype(str).to_numpy()
        splitter = GroupShuffleSplit(n_splits=1, test_size=validation_fraction, random_state=seed)
        train_index, validation_index = next(splitter.split(included, included["target"], groups))
        train = included.iloc[train_index].copy()
        validation = included.iloc[validation_index].copy()
        if set(train["patient_id"]) & set(validation["patient_id"]):
            raise ValueError("Patient leakage detected between development train and validation")
        split_map = {str(image_id): "train" for image_id in train["image_id"]}
        split_map.update({str(image_id): "validation" for image_id in validation["image_id"]})
        included["split"] = included["image_id"].map(split_map)
        train = included.loc[included["split"] == "train"].sort_values("image_id")
        validation = included.loc[included["split"] == "validation"].sort_values("image_id")
    else:
        train = included.copy()
        validation = included.copy()

    out_dir.mkdir(parents=True, exist_ok=False)
    columns = list(all_rows.columns)
    if "task" not in columns:
        columns.append("task")
    if "data_provenance" not in columns:
        columns.append("data_provenance")
    if "modality" not in columns:
        columns.append("modality")
    if "split" not in columns:
        columns.append("split")
    for frame in (included, train, validation):
        for column in columns:
            if column not in frame:
                frame[column] = pd.Series(dtype="object")
    included[columns].sort_values("image_id").to_csv(out_dir / "included_development.csv", index=False)
    train[columns].to_csv(out_dir / "train.csv", index=False)
    validation[columns].to_csv(out_dir / "validation.csv", index=False)
    excluded_rows[columns[: len(all_rows.columns)] + ["exclusion_reason"]].sort_values("image_id").to_csv(
        out_dir / "excluded_development.csv", index=False
    )

    report = {
        "task": "isic2020_melanoma_vs_nonmelanoma_v1",
        "status": "ready" if len(included) else "blocked_no_eligible_development_rows",
        "data_provenance": "genuine_isic_development",
        "label_mapping": LABELS,
        "source_all_manifest": str(all_manifest.resolve()),
        "source_all_manifest_sha256": sha256(all_manifest),
        "frozen_external_manifest": str(external_manifest.resolve()),
        "frozen_external_manifest_sha256": sha256(external_manifest),
        "review_report": str(review_report.resolve()),
        "review_report_sha256": sha256(review_report),
        "unresolved_policy": unresolved_policy,
        "seed": seed,
        "validation_fraction": validation_fraction,
        "source_rows": int(len(all_rows)),
        "source_labeled_rows": int((all_rows["diagnosis"].astype(str).str.lower() != "unknown").sum()),
        "frozen_external_rows_excluded": int(len(external_ids)),
        "official_or_exact_duplicate_rows_excluded": int(len(excluded_ids)),
        "confirmed_overlap_left_rows_excluded": int(len(confirmed_ids)),
        "unresolved_overlap_left_rows_excluded": int(len(unresolved_ids)) if unresolved_policy == "exclude" else 0,
        "eligible_development_rows": int(len(included)),
        "eligible_development_patients": int(included["patient_id"].nunique()) if not included.empty else 0,
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "train_patients": int(train["patient_id"].nunique()) if not train.empty else 0,
        "validation_patients": int(validation["patient_id"].nunique()) if not validation.empty else 0,
        "external_manifest_used_for_development": False,
        "notes": [
            "The frozen external manifest is excluded before splitting and is never used for development.",
            "Unknown diagnosis rows are not converted into labels.",
            "Unresolved perceptual candidates are conservatively excluded by default.",
            "No training was started by this preparation step.",
        ],
    }
    (out_dir / "task_readiness.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-manifest", type=Path, required=True)
    parser.add_argument("--external-manifest", type=Path, required=True)
    parser.add_argument("--excluded-manifest", type=Path, required=True)
    parser.add_argument("--review-report", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--unresolved-policy", choices=["exclude", "retain_with_disclosure"], default="exclude")
    args = parser.parse_args()
    try:
        report = prepare(
            args.all_manifest,
            args.external_manifest,
            args.excluded_manifest,
            args.review_report,
            args.out_dir,
            args.seed,
            args.validation_fraction,
            args.unresolved_policy,
        )
    except (OSError, ValueError, KeyError, FileExistsError) as error:
        print(f"ISIC DEVELOPMENT PREPARATION BLOCKED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
