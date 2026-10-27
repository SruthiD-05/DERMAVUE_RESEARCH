from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class JsonStore:
    """Small persistent store for the local research workspace API."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self._write({"patients": [], "cases": [], "images": []})

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {"patients": [], "cases": [], "images": []}
        except (OSError, json.JSONDecodeError):
            return {"patients": [], "cases": [], "images": []}

    def _write(self, value: dict[str, list[dict[str, Any]]]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def list(self, collection: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._read().get(collection, []))

    def get(self, collection: str, item_id: str) -> dict[str, Any] | None:
        return next((item for item in self.list(collection) if item.get("id") == item_id), None)

    def upsert(self, collection: str, item: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            rows = data.setdefault(collection, [])
            rows[:] = [row for row in rows if row.get("id") != item.get("id")]
            rows.insert(0, item)
            self._write(data)
            return item

    def patch(self, collection: str, item_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            item = self.get(collection, item_id)
            if item is None:
                return None
            item.update(changes)
            return self.upsert(collection, item)

    def delete(self, collection: str, item_id: str) -> bool:
        with self._lock:
            data = self._read()
            rows = data.setdefault(collection, [])
            before = len(rows)
            data[collection] = [row for row in rows if row.get("id") != item_id]
            if len(data[collection]) != before:
                self._write(data)
                return True
            return False

    def delete_where(self, collection: str, key: str, value: Any) -> None:
        with self._lock:
            data = self._read()
            data[collection] = [row for row in data.setdefault(collection, []) if row.get(key) != value]
            self._write(data)
