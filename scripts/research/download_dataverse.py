"""Resumable, checksum-verifying downloads from an official Dataverse release."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(url: str, destination: Path) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "DermaVue-research/0.1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as error:
        if error.code == 416:
            partial.unlink(missing_ok=True)
            return fetch(url, destination)
        raise
    mode = "ab" if offset and getattr(response, "status", 200) == 206 else "wb"
    if mode == "wb":
        offset = 0
    with partial.open(mode) as handle:
        shutil.copyfileobj(response, handle, length=1024 * 1024)
    partial.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persistent-id", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--file", action="append", required=True, dest="files")
    args = parser.parse_args()
    encoded = urllib.parse.quote(args.persistent_id, safe="")
    api_url = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={encoded}"
    api_request = urllib.request.Request(api_url, headers={"User-Agent": "DermaVue-research/0.1"})
    dataset = json.load(urllib.request.urlopen(api_request, timeout=60))
    available = {item["dataFile"]["filename"]: item["dataFile"] for item in dataset["data"]["latestVersion"]["files"]}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {"persistent_id": args.persistent_id, "api_url": api_url, "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": []}
    for filename in args.files:
        if filename not in available:
            print(f"Unknown file in Dataverse release: {filename}", file=sys.stderr)
            return 2
        item = available[filename]
        destination = args.out_dir / filename
        # Dataverse's default tabular rendering can normalize line endings and
        # separators. Request the original stored representation so the
        # repository checksum can be verified byte-for-byte.
        url = f"https://dataverse.harvard.edu/api/access/datafile/{item['id']}?format=original"
        expected = item.get("checksum", {}).get("value")
        if destination.exists() and expected and md5(destination) == expected:
            status = "already_verified"
        else:
            print(f"Downloading {filename} from official Dataverse file {item['id']} ...")
            fetch(url, destination)
            actual = md5(destination)
            if expected and actual != expected:
                destination.unlink(missing_ok=True)
                raise RuntimeError(f"Checksum mismatch for {filename}: expected {expected}, got {actual}")
            status = "downloaded_verified"
        report["files"].append({"id": item["id"], "filename": filename, "bytes": destination.stat().st_size, "checksum_type": "MD5", "checksum": expected, "source_url": url, "status": status})
    (args.out_dir / "acquisition_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
