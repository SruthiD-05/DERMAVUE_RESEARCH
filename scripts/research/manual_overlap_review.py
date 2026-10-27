"""Resumable visual review workflow for perceptual cross-dataset candidates.

This utility is a research-only review aid. It never changes the source
overlap audit, manifests, or image files. New decisions are written to a
separate versioned JSON file and default to unreviewed until a reviewer
explicitly records a disposition.

Examples:

  py -3.12 scripts/research/manual_overlap_review.py init
  py -3.12 scripts/research/manual_overlap_review.py serve --review-file REVIEW
  py -3.12 scripts/research/manual_overlap_review.py summarize --audit AUDIT
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import cv2
import pandas as pd

DISPOSITIONS = {"confirmed_duplicate", "not_duplicate", "uncertain", "unreviewed"}
SCHEMA_VERSION = "isic2020_ham10000_overlap_review_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _value(row: dict, *names: str):
    for name in names:
        value = row.get(name)
        if value is not None and str(value) not in {"", "nan", "NaN"}:
            return value
    return None


def _read_index(path: Path, source: str) -> dict[str, dict]:
    frame = pd.read_csv(path)
    if "image_id" not in frame or "image_path" not in frame:
        raise ValueError(f"{source} manifest requires image_id and image_path")
    if frame["image_id"].duplicated().any():
        raise ValueError(f"{source} manifest contains duplicate image_id values")
    return {str(row["image_id"]): row.to_dict() for _, row in frame.iterrows()}


def _image_info(path: Path) -> dict:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not decode review image: {path}")
    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else int(image.shape[2])
    return {"width": int(width), "height": int(height), "channels": channels}


def _diagnostic(row: dict, side: str) -> dict:
    if side == "left":
        return {
            "dataset": "isic2020",
            "data_provenance": "genuine_external",
            "patient_id": _value(row, "patient_id"),
            "lesion_id": _value(row, "lesion_id"),
            "diagnosis": _value(row, "diagnosis"),
            "benign_malignant": _value(row, "benign_malignant"),
            "target": _value(row, "target", "external_binary_label"),
            "sex": _value(row, "sex"),
            "age": _value(row, "age", "age_approx"),
            "localization": _value(row, "localization", "anatom_site_general_challenge"),
        }
    return {
        "dataset": "ham10000",
        "data_provenance": "genuine_ham10000",
        "patient_id": _value(row, "patient_id"),
        "lesion_id": _value(row, "lesion_id"),
        "diagnosis": _value(row, "dx", "diagnosis"),
        "diagnosis_type": _value(row, "dx_type"),
        "risk_label": _value(row, "risk_label"),
        "sex": _value(row, "sex"),
        "age": _value(row, "age"),
        "localization": _value(row, "localization"),
        "split": _value(row, "split"),
    }


def _candidate_record(item: dict, left_rows: dict[str, dict], right_rows: dict[str, dict]) -> dict:
    left_id = str(item["left_image_id"])
    right_id = str(item["right_image_id"])
    if left_id not in left_rows or right_id not in right_rows:
        raise ValueError(f"Audit pair is absent from supplied manifests: {left_id}, {right_id}")
    left = left_rows[left_id]
    right = right_rows[right_id]
    left_path = Path(str(left["image_path"])).resolve()
    right_path = Path(str(right["image_path"])).resolve()
    if not left_path.is_file() or not right_path.is_file():
        raise FileNotFoundError(f"Missing review image pair: {left_path}, {right_path}")
    return {
        "candidate_id": f"{left_id}__{right_id}",
        "left": {
            "source": "isic2020_all",
            "image_id": left_id,
            "image_path": str(left_path),
            "image_sha256": _value(left, "image_sha256"),
            "dimensions": _image_info(left_path),
            "diagnostic": _diagnostic(left, "left"),
        },
        "right": {
            "source": "ham10000_v4_all",
            "image_id": right_id,
            "image_path": str(right_path),
            "image_sha256": _value(right, "image_sha256"),
            "dimensions": _image_info(right_path),
            "diagnostic": _diagnostic(right, "right"),
        },
        "hamming_distance": int(item["hamming_distance"]),
        "disposition": "unreviewed",
        "reviewer": "",
        "review_date_utc": "",
        "rationale": "",
    }


def init_review(audit_path: Path, left_manifest: Path, right_manifests: list[Path], out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing review file: {out}")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    left_rows = _read_index(left_manifest, "left")
    right_rows: dict[str, dict] = {}
    for path in right_manifests:
        index = _read_index(path, "right")
        overlap = set(right_rows).intersection(index)
        if overlap:
            raise ValueError(f"Right manifests overlap on image IDs: {sorted(overlap)[:5]}")
        right_rows.update(index)
    candidates = [_candidate_record(item, left_rows, right_rows) for item in audit.get("perceptual_cross_dataset_matches", [])]
    candidate_ids = [item["candidate_id"] for item in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Audit contains duplicate perceptual candidate pairs")
    now = _utc_now()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "review_status": "pending",
        "source_audit": str(audit_path.resolve()),
        "source_audit_sha256": _sha256(audit_path),
        "source_audit_exact_match_count": int(audit.get("exact_cross_dataset_match_count", 0)),
        "source_audit_perceptual_candidate_count": len(candidates),
        "created_at_utc": now,
        "updated_at_utc": now,
        "review_policy": {
            "dispositions": sorted(DISPOSITIONS),
            "similarity_is_not_confirmation": True,
            "confirmed_duplicates_require_exclusion_or_explicit_accounting": True,
            "unreviewed_and_uncertain_pairs_remain_explicitly_disclosed": True,
        },
        "candidates": candidates,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _atomic_write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _load_review(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported review schema: {payload.get('schema_version')}")
    for item in payload.get("candidates", []):
        if item.get("disposition") not in DISPOSITIONS:
            raise ValueError(f"Invalid disposition for {item.get('candidate_id')}")
    return payload


def summarize(audit_path: Path, review_path: Path, out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing overlap review report: {out}")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    review = _load_review(review_path)
    expected_hash = _sha256(audit_path)
    if review.get("source_audit_sha256") != expected_hash:
        raise ValueError("Review file was created from a different source audit")
    candidates = review["candidates"]
    counts = {name: sum(item["disposition"] == name for item in candidates) for name in sorted(DISPOSITIONS)}
    confirmed = [
        {
            "candidate_id": item["candidate_id"],
            "left_image_id": item["left"]["image_id"],
            "right_image_id": item["right"]["image_id"],
            "hamming_distance": item["hamming_distance"],
            "reviewer": item["reviewer"],
            "review_date_utc": item["review_date_utc"],
            "rationale": item["rationale"],
        }
        for item in candidates if item["disposition"] == "confirmed_duplicate"
    ]
    unresolved = [
        {
            "candidate_id": item["candidate_id"],
            "left_image_id": item["left"]["image_id"],
            "right_image_id": item["right"]["image_id"],
            "hamming_distance": item["hamming_distance"],
            "disposition": item["disposition"],
        }
        for item in candidates if item["disposition"] in {"uncertain", "unreviewed"}
    ]
    review_complete = counts["unreviewed"] == 0 and counts["uncertain"] == 0
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_status": "complete" if review_complete else "review_incomplete",
        "source_audit": str(audit_path.resolve()),
        "source_audit_sha256": expected_hash,
        "review_file": str(review_path.resolve()),
        "review_file_sha256": _sha256(review_path),
        "exact_cross_dataset_match_count": int(audit.get("exact_cross_dataset_match_count", 0)),
        "perceptual_candidate_count": len(candidates),
        "reviewed_candidate_count": len(candidates) - counts["unreviewed"],
        "disposition_counts": counts,
        "confirmed_duplicates": confirmed,
        "unresolved_candidates": unresolved,
        "independence_status": (
            "review_resolved_but_confirmed_duplicates_require_exclusion_policy"
            if review_complete and counts["confirmed_duplicate"]
            else "review_resolved_no_confirmed_perceptual_duplicates"
            if review_complete
            else "blocked_review_incomplete"
        ),
        "note": "Perceptual similarity alone never creates a duplicate decision. Exact matches and confirmed duplicates must be excluded or explicitly accounted for before an independence claim.",
        "generated_at_utc": _utc_now(),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DermaVue overlap review</title>
<style>
body { font-family: system-ui, sans-serif; margin: 0; color: #18212b; background: #f5f7fa; }
header { padding: 14px 22px; background: #172a3a; color: white; }
main { padding: 18px 22px; max-width: 1500px; margin: auto; }
.toolbar, .review { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin: 12px 0; }
button { padding: 9px 12px; border: 1px solid #9aa9b6; border-radius: 6px; background: white; cursor: pointer; }
button.active { background: #176b87; color: white; border-color: #176b87; }
input, textarea { padding: 8px; border: 1px solid #aab5bf; border-radius: 5px; }
textarea { width: min(720px, 100%); min-height: 70px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.card { background: white; padding: 12px; border-radius: 8px; box-shadow: 0 1px 4px #0002; }
.card img { display: block; width: 100%; height: 430px; object-fit: contain; background: #101820; }
pre { white-space: pre-wrap; font-size: 12px; }
.muted { color: #5e6b75; }
@media (max-width: 900px) { .pair { grid-template-columns: 1fr; } .card img { height: 320px; } }
</style>
</head>
<body>
<header><strong>DermaVue — ISIC 2020 / HAM10000 perceptual-overlap review</strong></header>
<main>
<p class="muted">Research utility only. Similarity is not confirmation. Decisions are saved to the versioned review file and can be resumed.</p>
<div class="toolbar">
  <button id="prev">Previous</button><button id="next">Next</button>
  <span id="position"></span><span id="counts"></span>
</div>
<section class="pair">
  <article class="card"><h2 id="left-title">ISIC 2020</h2><img id="left-image" alt="ISIC candidate"></article>
  <article class="card"><h2 id="right-title">HAM10000</h2><img id="right-image" alt="HAM10000 candidate"></article>
</section>
<section class="card">
  <p id="distance"></p><div id="metadata" class="pair"></div>
  <div class="review">
    <label>Reviewer <input id="reviewer" autocomplete="off"></label>
    <button data-disposition="confirmed_duplicate">Confirmed duplicate</button>
    <button data-disposition="not_duplicate">Not duplicate</button>
    <button data-disposition="uncertain">Uncertain</button>
    <button data-disposition="unreviewed">Leave unreviewed</button>
  </div>
  <label>Rationale<br><textarea id="rationale"></textarea></label>
  <p id="saved" class="muted"></p>
</section>
</main>
<script>
let state = null, index = 0;
const esc = (value) => String(value ?? "—");
function firstUnreviewed() {
  const found = state.candidates.findIndex(x => x.disposition === "unreviewed");
  return found < 0 ? 0 : found;
}
function renderMetadata(item) {
  const block = (side, title) => {
    const d = item[side].diagnostic;
    return "<div><h3>" + title + ": " + esc(item[side].image_id) + "</h3><pre>" +
      esc(JSON.stringify({provenance: item[side].source, dimensions: item[side].dimensions, sha256: item[side].image_sha256, diagnostic: d}, null, 2)) +
      "</pre></div>";
  };
  document.getElementById("metadata").innerHTML = block("left", "ISIC 2020") + block("right", "HAM10000");
}
function render() {
  const item = state.candidates[index];
  document.getElementById("position").textContent = "Candidate " + (index + 1) + " / " + state.candidates.length;
  const counts = {};
  state.candidates.forEach(x => counts[x.disposition] = (counts[x.disposition] || 0) + 1);
  document.getElementById("counts").textContent = " | unreviewed " + (counts.unreviewed || 0) + ", confirmed " + (counts.confirmed_duplicate || 0) + ", rejected " + (counts.not_duplicate || 0) + ", uncertain " + (counts.uncertain || 0);
  document.getElementById("left-image").src = "/image/" + encodeURIComponent(item.candidate_id) + "/left";
  document.getElementById("right-image").src = "/image/" + encodeURIComponent(item.candidate_id) + "/right";
  document.getElementById("distance").textContent = "Pair " + item.candidate_id + "; DCT Hamming distance " + item.hamming_distance;
  renderMetadata(item);
  document.getElementById("reviewer").value = item.reviewer || "";
  document.getElementById("rationale").value = item.rationale || "";
  document.querySelectorAll("[data-disposition]").forEach(button => button.classList.toggle("active", button.dataset.disposition === item.disposition));
}
async function save(disposition) {
  const item = state.candidates[index];
  const response = await fetch("/api/review", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
    candidate_id: item.candidate_id, disposition: disposition,
    reviewer: document.getElementById("reviewer").value,
    rationale: document.getElementById("rationale").value
  })});
  if (!response.ok) { document.getElementById("saved").textContent = "Save failed"; return; }
  state = await response.json();
  index = state.candidates.findIndex(x => x.candidate_id === item.candidate_id);
  document.getElementById("saved").textContent = "Saved at " + new Date().toISOString();
  render();
}
document.getElementById("prev").onclick = () => { index = Math.max(0, index - 1); render(); };
document.getElementById("next").onclick = () => { index = Math.min(state.candidates.length - 1, index + 1); render(); };
document.querySelectorAll("[data-disposition]").forEach(button => button.onclick = () => save(button.dataset.disposition));
fetch("/api/state").then(r => r.json()).then(payload => { state = payload; index = firstUnreviewed(); render(); });
</script>
</body>
</html>"""


class _ReviewHandler(BaseHTTPRequestHandler):
    server_version = "DermaVueOverlapReview/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[overlap-review] {self.address_string()} - {fmt % args}")

    @property
    def review_file(self) -> Path:
        return self.server.review_file  # type: ignore[attr-defined]

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/state":
            self._send(200, self.review_file.read_bytes(), "application/json")
            return
        parts = [unquote(part) for part in parsed.path.split("/") if part]
        if len(parts) == 3 and parts[0] == "image" and parts[2] in {"left", "right"}:
            state = _load_review(self.review_file)
            item = next((x for x in state["candidates"] if x["candidate_id"] == parts[1]), None)
            if item is None:
                self._send(404, b"Unknown candidate", "text/plain; charset=utf-8")
                return
            path = Path(item[parts[2]]["image_path"])
            if not path.is_file():
                self._send(404, b"Image not found", "text/plain; charset=utf-8")
                return
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self._send(200, path.read_bytes(), content_type)
            return
        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/review":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            disposition = str(body.get("disposition", ""))
            candidate_id = str(body.get("candidate_id", ""))
            reviewer = str(body.get("reviewer", "")).strip()
            rationale = str(body.get("rationale", "")).strip()
            if disposition not in DISPOSITIONS:
                raise ValueError("invalid disposition")
            if disposition != "unreviewed" and not reviewer:
                raise ValueError("reviewer is required for a review disposition")
            state = _load_review(self.review_file)
            item = next((x for x in state["candidates"] if x["candidate_id"] == candidate_id), None)
            if item is None:
                raise ValueError("unknown candidate_id")
            item["disposition"] = disposition
            item["reviewer"] = reviewer
            item["review_date_utc"] = _utc_now() if disposition != "unreviewed" else ""
            item["rationale"] = rationale
            state["updated_at_utc"] = _utc_now()
            state["review_status"] = "complete" if all(x["disposition"] not in {"unreviewed", "uncertain"} for x in state["candidates"]) else "pending"
            _atomic_write(self.review_file, state)
            self._send(200, json.dumps(state, indent=2).encode("utf-8"), "application/json")
        except (ValueError, json.JSONDecodeError, OSError) as error:
            self._send(400, str(error).encode("utf-8"), "text/plain; charset=utf-8")


def serve(review_file: Path, host: str, port: int) -> None:
    if not review_file.is_file():
        raise FileNotFoundError(review_file)
    server = ThreadingHTTPServer((host, port), _ReviewHandler)
    server.review_file = review_file.resolve()  # type: ignore[attr-defined]
    print(f"Overlap review utility listening on http://{host}:{port}")
    print("Press Ctrl+C to stop. Review decisions are persisted after each save.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--audit", type=Path, required=True)
    init.add_argument("--left-manifest", type=Path, required=True)
    init.add_argument("--right-manifest", type=Path, action="append", required=True)
    init.add_argument("--out", type=Path, required=True)
    summary = sub.add_parser("summarize")
    summary.add_argument("--audit", type=Path, required=True)
    summary.add_argument("--review-file", type=Path, required=True)
    summary.add_argument("--out", type=Path, required=True)
    server = sub.add_parser("serve")
    server.add_argument("--review-file", type=Path, required=True)
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        if args.command == "init":
            print(json.dumps(init_review(args.audit, args.left_manifest, args.right_manifest, args.out), indent=2))
        elif args.command == "summarize":
            print(json.dumps(summarize(args.audit, args.review_file, args.out), indent=2))
        else:
            serve(args.review_file, args.host, args.port)
    except (OSError, ValueError, KeyError, FileExistsError) as error:
        print(f"OVERLAP REVIEW FAILED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
