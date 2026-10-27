"""Record immutable-file provenance and SHA-256 checksums for ISIC 2020."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--duplicates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    files = [args.archive, args.metadata, args.duplicates]
    if any(not path.is_file() for path in files):
        missing = [str(path) for path in files if not path.is_file()]
        raise SystemExit(f"Missing acquired file(s): {missing}")
    expected_archive_bytes = 24707698022
    if args.archive.stat().st_size != expected_archive_bytes:
        raise SystemExit(
            f"Archive length mismatch: expected {expected_archive_bytes}, "
            f"found {args.archive.stat().st_size}"
        )
    payload = {
        "dataset_id": "isic2020",
        "dataset_version": "ISIC 2020 Challenge Dataset",
        "source_url": "https://challenge.isic-archive.com/data/",
        "archive_url": "https://isic-archive.s3.amazonaws.com/challenges/2020/ISIC_2020_Training_JPEG.zip",
        "terms_url": "https://challenge.isic-archive.com/terms-of-use/",
        "access_date_utc": datetime.now(timezone.utc).isoformat(),
        "license_note": "The official ISIC portal identifies the 2020 release as CC-BY-NC 4.0; research use remains subject to the source terms and attribution requirements.",
        "acquisition_status": "official_archive_and_ground_truth_verified",
        "official_archive_http_metadata": {
            "content_length_bytes": 24707698022,
            "etag": "ebb879d3b9be0f5b4515e28dc8ebbb88-472",
            "last_modified": "Fri, 19 Sep 2025 21:40:40 GMT",
            "note": "S3 multipart ETag is recorded as source metadata and is not treated as a SHA-256 checksum.",
        },
        "files": {},
        "software": {"python": platform.python_version(), "platform": platform.platform()},
        "notes": [
            "Original downloaded files are preserved without modification.",
            "The image archive must be extracted into a source-specific images directory; extracted files are derivatives, not replacements for the archive.",
            "Independent-validation status remains blocked until perceptual-review candidates are dispositioned and model compatibility passes.",
        ],
    }
    for path in files:
        payload["files"][path.name] = {
            "path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
