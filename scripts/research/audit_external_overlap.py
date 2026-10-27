"""Audit exact and perceptual overlap between frozen dataset manifests.

The report is diagnostic.  It never changes a manifest or removes an image.
Perceptual matches are conservative review candidates and do not establish
provenance on their own.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def _phash(path: Path) -> int:
    # JPEG-native reduced decoding avoids loading full 6000x4000 frames for
    # the review hash while retaining a deterministic low-resolution signal.
    image = cv2.imread(str(path), cv2.IMREAD_REDUCED_GRAYSCALE_8)
    if image is None:
        raise ValueError(f"could not decode image: {path}")
    small = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA).astype("float32")
    dct = cv2.dct(small)
    low = dct[:8, :8]
    threshold = float(np.median(low[1:, 1:]))
    bits = 0
    for value in low.ravel():
        bits = (bits << 1) | int(value >= threshold)
    return bits


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest(path: Path, source: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"image_id", "image_path"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source} manifest is missing columns: {missing}")
    frame = frame.copy()
    frame["source"] = source
    frame["image_path"] = frame["image_path"].map(lambda value: str(Path(value).resolve()))
    return frame


def audit(left_manifest: Path, left_name: str, right_manifests: list[Path], right_name: str, max_distance: int = 4) -> dict:
    left = _manifest(left_manifest, left_name)
    right = pd.concat([_manifest(path, right_name) for path in right_manifests], ignore_index=True)
    rows = []
    for frame in (left, right):
        for row in frame.itertuples(index=False):
            path = Path(row.image_path)
            if not path.is_file():
                raise FileNotFoundError(path)
            manifest_hash = getattr(row, "image_sha256", None)
            rows.append({
                "source": row.source,
                "image_id": row.image_id,
                "image_path": str(path),
                "sha256": str(manifest_hash) if manifest_hash and str(manifest_hash) != "nan" else _sha256(path),
                "phash": _phash(path),
            })
    left_rows = [row for row in rows if row["source"] == left_name]
    right_rows = [row for row in rows if row["source"] == right_name]
    right_by_hash = {}
    for row in right_rows:
        right_by_hash.setdefault(row["sha256"], []).append(row)
    exact = []
    for row in left_rows:
        for match in right_by_hash.get(row["sha256"], []):
            exact.append({"left_image_id": row["image_id"], "right_image_id": match["image_id"], "sha256": row["sha256"]})

    # Bucket by each 16-bit segment. Any 64-bit pair within <=4 Hamming bits
    # shares at least one exact 16-bit segment, avoiding quadratic comparison.
    buckets: dict[tuple[int, int], list[dict]] = {}
    for row in right_rows:
        value = row["phash"]
        for segment in range(4):
            key = (segment, (value >> (segment * 16)) & 0xFFFF)
            buckets.setdefault(key, []).append(row)
    perceptual = []
    seen = set()
    for row in left_rows:
        candidates = []
        for segment in range(4):
            key = (segment, (row["phash"] >> (segment * 16)) & 0xFFFF)
            candidates.extend(buckets.get(key, []))
        for match in candidates:
            key = (row["image_id"], match["image_id"])
            if key in seen or row["sha256"] == match["sha256"]:
                continue
            seen.add(key)
            distance = (row["phash"] ^ match["phash"]).bit_count()
            if distance <= max_distance:
                perceptual.append({"left_image_id": row["image_id"], "right_image_id": match["image_id"], "hamming_distance": distance})
    return {
        "left_source": left_name,
        "right_source": right_name,
        "left_manifest": str(left_manifest.resolve()),
        "right_manifests": [str(path.resolve()) for path in right_manifests],
        "left_rows": len(left_rows),
        "right_rows": len(right_rows),
        "exact_cross_dataset_matches": exact,
        "exact_cross_dataset_match_count": len(exact),
        "perceptual_cross_dataset_matches": perceptual,
        "perceptual_cross_dataset_match_count": len(perceptual),
        "perceptual_threshold_hamming_distance": max_distance,
        "interpretation": "Exact matches are conservative overlap evidence. Perceptual matches require manual review and are not automatic exclusions or proof of common provenance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-manifest", type=Path, required=True)
    parser.add_argument("--left-name", required=True)
    parser.add_argument("--right-manifest", type=Path, action="append", required=True)
    parser.add_argument("--right-name", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-distance", type=int, default=4)
    args = parser.parse_args()
    report = audit(args.left_manifest, args.left_name, args.right_manifest, args.right_name, args.max_distance)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
