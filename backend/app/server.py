from __future__ import annotations

import json
import re
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .model_adapter import V2ModelAdapter
from .partner_adapter import PartnerAdapterError, PartnerInvalidInput
from .store import JsonStore

ROOT = Path(__file__).resolve().parents[1]
adapter = V2ModelAdapter()
store = JsonStore(ROOT / "data" / "records.json")


class Handler(BaseHTTPRequestHandler):
    server_version = "DermaVueBackend/0.2"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[backend] {self.address_string()} - {fmt % args}")

    def _send(self, status: int, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> object:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _multipart(self) -> tuple[list[bytes], list[str], dict[str, str]]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 60 * 1024 * 1024:
            raise PartnerInvalidInput("Request body is empty or exceeds the 60 MB limit.")
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise PartnerInvalidInput("Analysis requires multipart/form-data.")
        raw = self.rfile.read(length)
        message = BytesParser(policy=default).parsebytes(b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw)
        images: list[bytes] = []
        image_ids: list[str] = []
        fields: dict[str, str] = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if name == "images":
                if part.get_content_type() not in {"image/jpeg", "image/png"}:
                    raise PartnerInvalidInput("Only JPG, JPEG, and PNG images are supported.")
                data = part.get_payload(decode=True) or b""
                if not data or len(data) > 15 * 1024 * 1024:
                    raise PartnerInvalidInput("Each image must be non-empty and no larger than 15 MB.")
                images.append(data)
            elif name == "image_ids":
                image_ids.append((part.get_payload(decode=True) or b"").decode("utf-8", "replace").strip())
            elif name in {"age", "sex", "localization"}:
                fields[name] = (part.get_payload(decode=True) or b"").decode("utf-8", "replace").strip()
        if not images or len(images) != len(image_ids) or any(not item for item in image_ids):
            raise PartnerInvalidInput("The request must contain matching images and image_ids fields.")
        return images, image_ids, fields

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        status = adapter.status()
        if path in {"/", "/health", "/api/health"}:
            self._send(HTTPStatus.OK, {"status": "ok", "service": "dermavue-backend", "model": status.__dict__})
            return
        if path == "/api/model/status":
            self._send(HTTPStatus.OK, {"state": status.state, "backendConfigured": True, "modelName": status.name, "modelVersion": status.version, "architecture": status.architecture, "artifactState": status.artifact_state, "loadState": status.load_state, "releaseState": status.release_state, "researchMode": status.research_mode, "metadataSource": status.metadata_source, "reportedMetrics": status.reported_metrics, "checkpointLoaded": status.checkpoint_loaded, "inferenceAvailable": status.inference_available, "message": status.message})
            return
        if path == "/api/model/info":
            self._send(HTTPStatus.OK, adapter.info())
            return
        parts = [part for part in path.split("/") if part]
        if parts == ["api", "patients"]:
            self._send(HTTPStatus.OK, store.list("patients"))
            return
        if len(parts) == 3 and parts[:2] == ["api", "patients"]:
            item = store.get("patients", parts[2])
            self._send(HTTPStatus.OK if item else HTTPStatus.NOT_FOUND, item or {"error": "not_found"})
            return
        if parts == ["api", "cases"]:
            self._send(HTTPStatus.OK, store.list("cases"))
            return
        if len(parts) == 3 and parts[:2] == ["api", "cases"]:
            item = store.get("cases", parts[2])
            self._send(HTTPStatus.OK if item else HTTPStatus.NOT_FOUND, item or {"error": "not_found"})
            return
        if len(parts) == 4 and parts[:2] == ["api", "cases"] and parts[3] == "images":
            self._send(HTTPStatus.OK, [i for i in store.list("images") if i.get("caseId") == parts[2]])
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": "Endpoint does not exist."})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/")
        if re.fullmatch(r"/api/cases/[^/]+/analyze", path):
            status = adapter.status()
            if not status.inference_available:
                self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "model_unavailable", "message": status.message})
                return
            case_id = path.split("/")[3]
            case = store.get("cases", case_id)
            if not case and not adapter.research_enabled():
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": "Case does not exist."})
                return
            try:
                images, image_ids, fields = self._multipart()
                known = {item.get("id") for item in store.list("images") if item.get("caseId") == case_id}
                if case and any(image_id not in known for image_id in image_ids):
                    raise PartnerInvalidInput("Every image_id must belong to the requested case.")
                patient = store.get("patients", case.get("patientId")) if case else {}
                age_text = fields.get("age") or str(patient.get("age") or "")
                age = float(age_text) if age_text else None
                if "sex" in fields:
                    sex = fields["sex"].lower()
                    if sex not in {"male", "female", "unknown"}:
                        raise PartnerInvalidInput("sex must be male, female, or unknown.")
                else:
                    sex = str(patient.get("sex") or "unknown").lower()
                    if sex not in {"male", "female", "unknown"}:
                        sex = "unknown"
                localization = (fields.get("localization") or str((case or {}).get("bodyRegion") or (case or {}).get("anatomicalSite") or "unknown")).lower()
                if localization not in set(adapter.partner.allowed_localizations()):
                    raise PartnerInvalidInput(f"Unknown localization '{localization}'.")
                result = adapter.partner.predict(images, image_ids, age=age, sex=sex, localization=localization, research_mode=adapter.research_enabled())
                result.update({"id": f"analysis-{case_id}", "caseId": case_id, "inferredAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()})
                self._send(HTTPStatus.OK, result)
            except PartnerInvalidInput as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_input", "message": str(exc)})
            except PartnerAdapterError as exc:
                self._send(HTTPStatus.BAD_GATEWAY, {"error": "inference_failed", "message": str(exc)})
            except (ValueError, TypeError):
                self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_input", "message": "Patient age must be numeric."})
            return
            return
        if path == "/api/patients":
            item = self._json_body()
            self._send(HTTPStatus.CREATED, store.upsert("patients", item if isinstance(item, dict) else {}))
            return
        if path == "/api/cases":
            item = self._json_body()
            if not isinstance(item, dict):
                self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_input", "message": "Case payload must be an object."})
                return
            reference = str(item.get("caseReference") or "").strip().lower()
            name = str(item.get("caseName") or "").strip().lower()
            existing = store.list("cases")
            if reference and any(str(row.get("caseReference") or "").strip().lower() == reference for row in existing):
                self._send(HTTPStatus.CONFLICT, {"error": "case_reference_conflict", "message": "That user-facing case ID is already in use."})
                return
            if name and any(str(row.get("caseName") or "").strip().lower() == name for row in existing):
                self._send(HTTPStatus.CONFLICT, {"error": "case_name_conflict", "message": "That user-facing case name is already in use."})
                return
            self._send(HTTPStatus.CREATED, store.upsert("cases", item))
            return
        match = re.fullmatch(r"/api/cases/([^/]+)/images", path)
        if match:
            payload = self._json_body()
            images = payload if isinstance(payload, list) else []
            for image in images:
                if isinstance(image, dict):
                    store.upsert("images", image)
            self._send(HTTPStatus.CREATED, images)
            return
        if re.fullmatch(r"/api/reports/[^/]+/export", path):
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "report_unavailable", "message": "Reports require a stored model result; V2 inference is unavailable."})
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": "Endpoint does not exist."})

    def do_PATCH(self) -> None:  # noqa: N802
        match = re.fullmatch(r"/api/(patients|cases)/([^/]+)", urlparse(self.path).path.rstrip("/"))
        if not match:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        changes = self._json_body()
        if match.group(1) == "cases" and isinstance(changes, dict):
            current_id = match.group(2)
            reference = str(changes.get("caseReference") or "").strip().lower()
            name = str(changes.get("caseName") or "").strip().lower()
            others = [row for row in store.list("cases") if row.get("id") != current_id]
            if reference and any(str(row.get("caseReference") or "").strip().lower() == reference for row in others):
                self._send(HTTPStatus.CONFLICT, {"error": "case_reference_conflict", "message": "That user-facing case ID is already in use."})
                return
            if name and any(str(row.get("caseName") or "").strip().lower() == name for row in others):
                self._send(HTTPStatus.CONFLICT, {"error": "case_name_conflict", "message": "That user-facing case name is already in use."})
                return
        item = store.patch(match.group(1), match.group(2), changes if isinstance(changes, dict) else {})
        self._send(HTTPStatus.OK if item else HTTPStatus.NOT_FOUND, item or {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        match = re.fullmatch(r"/api/(patients|cases)/([^/]+)", urlparse(self.path).path.rstrip("/"))
        if not match:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        collection, item_id = match.groups()
        deleted = store.delete(collection, item_id)
        if collection == "cases":
            store.delete_where("images", "caseId", item_id)
        self._send(HTTPStatus.NO_CONTENT if deleted else HTTPStatus.NOT_FOUND, {})


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    if adapter.research_enabled() and host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("Local research inference may only bind to loopback.")
    if adapter.research_enabled():
        try:
            adapter.load_research_model()
        except Exception as exc:
            print(f"Local research inference unavailable: {exc}")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"DermaVue backend listening on http://{host}:{port}")
    print(adapter.status().message)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping backend")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
