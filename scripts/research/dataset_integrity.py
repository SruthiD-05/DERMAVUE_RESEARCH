"""Report exact and perceptual image duplicates for research datasets.

The report is diagnostic only. It never deletes, relabels, or moves data.
Perceptual matches are candidates for manual review, not automatic exclusions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def exact_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def perceptual_hash(path: Path) -> str:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("image could not be decoded")
    small = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)
    threshold = float(small.mean())
    return "".join("1" if value >= threshold else "0" for value in small.ravel())


def hamming_distance(left: str, right: str) -> int:
    return sum(a != b for a, b in zip(left, right))


def inspect_sources(sources: list[tuple[str, Path]], max_perceptual_distance: int = 4) -> dict:
    rows = []
    errors = []
    for source_name, directory in sources:
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            try:
                rows.append({
                    "source": source_name,
                    "path": str(path.resolve()),
                    "sha256": exact_hash(path),
                    "phash": perceptual_hash(path),
                })
            except (OSError, ValueError) as error:
                errors.append({"path": str(path), "error": str(error)})

    exact_groups = {}
    for row in rows:
        exact_groups.setdefault(row["sha256"], []).append(row["path"])
    exact_duplicates = [paths for paths in exact_groups.values() if len(paths) > 1]

    perceptual_matches = []
    for index, left in enumerate(rows):
        for right in rows[index + 1:]:
            distance = hamming_distance(left["phash"], right["phash"])
            if distance <= max_perceptual_distance and left["sha256"] != right["sha256"]:
                perceptual_matches.append({"left": left["path"], "right": right["path"], "distance": distance})

    return {
        "image_count": len(rows),
        "decode_error_count": len(errors),
        "decode_errors": errors,
        "exact_duplicate_groups": exact_duplicates,
        "perceptual_match_count": len(perceptual_matches),
        "perceptual_matches": perceptual_matches,
        "note": "Perceptual matches require manual review; no files or labels were changed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True, help="name=directory; repeat for each source")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-perceptual-distance", type=int, default=4)
    args = parser.parse_args()
    sources = []
    for value in args.source:
        if "=" not in value:
            parser.error("--source must use name=directory")
        name, directory = value.split("=", 1)
        path = Path(directory)
        if not path.is_dir():
            parser.error(f"source directory does not exist: {path}")
        sources.append((name, path))
    report = inspect_sources(sources, args.max_perceptual_distance)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
