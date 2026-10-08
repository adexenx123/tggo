from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class InboxStore:
    def __init__(self, root: Path):
        self.root = root.expanduser()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        self.index_path = self.root / "index.json"
        if not self.index_path.exists():
            self._write_index({"items": {}, "updates": {}, "offset": 0})

    def _read_index(self) -> dict[str, Any]:
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _write_index(self, index: dict[str, Any]) -> None:
        temporary = self.root / "index.json.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(index, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.index_path)
        os.chmod(self.index_path, 0o600)

    def create(self, record: dict[str, Any], attachment_source: Path | None = None) -> dict[str, Any]:
        index = self._read_index()
        update_key = str(record["update_id"])
        existing = index["updates"].get(update_key)
        if existing:
            return self.get(existing)
        identifier = "TG-" + hashlib.sha256(update_key.encode()).hexdigest()[:12].upper()
        item_directory = self.root / identifier
        item_directory.mkdir(mode=0o700)
        os.chmod(item_directory, 0o700)
        immutable = dict(record)
        immutable.update({"id": identifier, "received_at": record.get("received_at") or datetime.now(timezone.utc).isoformat()})
        record_path = item_directory / "record.json"
        descriptor = os.open(record_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(immutable, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
        if attachment_source is not None:
            relative = Path(str(immutable["attachment"]["path"]))
            files = item_directory / "files"
            files.mkdir(mode=0o700)
            destination = files / relative.name
            os.replace(attachment_source, destination)
            os.chmod(destination, 0o600)
        index["items"][identifier] = {"read": False, "archived": False}
        index["updates"][update_key] = identifier
        self._write_index(index)
        return self.get(identifier)

    def get(self, identifier: str) -> dict[str, Any]:
        index = self._read_index()
        state = index["items"].get(identifier)
        if state is None:
            raise KeyError(identifier)
        record = json.loads((self.root / identifier / "record.json").read_text(encoding="utf-8"))
        return {**record, **state}

    def list(self, include_archived: bool = False) -> list[dict[str, Any]]:
        index = self._read_index()
        records = [self.get(identifier) for identifier in index["items"]]
        if not include_archived:
            records = [record for record in records if not record["archived"]]
        return sorted(records, key=lambda record: (record["received_at"], record["id"]), reverse=True)

    def _set_state(self, identifier: str, key: str) -> dict[str, Any]:
        index = self._read_index()
        if identifier not in index["items"]:
            raise KeyError(identifier)
        index["items"][identifier][key] = True
        self._write_index(index)
        return self.get(identifier)

    def mark_read(self, identifier: str) -> dict[str, Any]:
        return self._set_state(identifier, "read")

    def archive(self, identifier: str) -> dict[str, Any]:
        return self._set_state(identifier, "archived")

    @property
    def offset(self) -> int:
        return int(self._read_index().get("offset", 0))

    def set_offset(self, offset: int) -> None:
        index = self._read_index()
        index["offset"] = int(offset)
        self._write_index(index)
