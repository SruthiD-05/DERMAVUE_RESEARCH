"""Linear decode/inventory validation for extracted ISIC 2020 JPEGs.

This deliberately does not perform an all-pairs perceptual comparison. Exact
duplicate accounting comes from the frozen manifest, and cross-dataset
perceptual review is handled by ``audit_external_overlap.py``.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import pandas as pd


def validate(images_dir: Path, manifest_path: Path, out: Path) -> dict:
    manifest = pd.read_csv(manifest_path)
    required = {"image_id", "image_path", "image_sha256", "image_name"}
    missing = sorted(required - set(manifest.columns))
    if missing:
        raise ValueError(f"Manifest is missing columns: {missing}")
    expected = set(manifest["image_id"].astype(str))
    files = sorted(path for path in images_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    found = {path.stem for path in files}
    missing_ids = sorted(expected - found)
    extra_ids = sorted(found - expected)
    decode_errors = []
    zero_byte_files = []
    dimensions = Counter()
    channels = Counter()
    for path in files:
        if path.stat().st_size == 0:
            zero_byte_files.append(str(path.resolve()))
            continue
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            decode_errors.append(str(path.resolve()))
            continue
        height, width = image.shape[:2]
        dimensions[f"{width}x{height}"] += 1
        channels[str(1 if image.ndim == 2 else image.shape[2])] += 1
    duplicate_groups = manifest.groupby("image_sha256")["image_id"].agg(list)
    exact_duplicate_groups = [ids for ids in duplicate_groups if len(ids) > 1]
    report = {
        "images_dir": str(images_dir.resolve()),
        "manifest": str(manifest_path.resolve()),
        "manifest_rows": int(len(manifest)),
        "image_files_found": int(len(files)),
        "missing_image_id_count": int(len(missing_ids)),
        "missing_image_ids": missing_ids[:100],
        "extra_image_id_count": int(len(extra_ids)),
        "extra_image_ids": extra_ids[:100],
        "decode_error_count": int(len(decode_errors)),
        "decode_errors": decode_errors[:100],
        "zero_byte_count": int(len(zero_byte_files)),
        "zero_byte_files": zero_byte_files[:100],
        "decoded_image_count": int(sum(dimensions.values())),
        "dimensions_top_20": dimensions.most_common(20),
        "channel_counts": dict(channels),
        "exact_duplicate_group_count_from_manifest": int(len(exact_duplicate_groups)),
        "exact_duplicate_image_count_from_manifest": int(sum(len(ids) for ids in exact_duplicate_groups)),
        "integrity_passed": bool(not missing_ids and not extra_ids and not decode_errors and not zero_byte_files),
        "note": "Exact duplicate groups are reported from the frozen manifest; no files or labels were changed.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate(args.images_dir, args.manifest, args.out)
    except (OSError, ValueError, KeyError) as error:
        print(f"IMAGE VALIDATION FAILED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
