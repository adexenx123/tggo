from __future__ import annotations

import hashlib
import os
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

from .files import sanitize_filename
from .inbound import InboundRequest, parse_update
from .inbox import InboxStore


class Receiver:
    def __init__(self, store: InboxStore, transport: object, chat_id: str, sleeper: Callable[[float], None] = time.sleep):
        self.store = store
        self.transport = transport
        self.chat_id = chat_id
        self.sleeper = sleeper
        self.stopped = False

    def _save(self, request: InboundRequest) -> dict:
        record = {"update_id": request.update_id, "message_id": request.message_id, "chat_id": request.chat_id, "text": request.text}
        temporary: Optional[Path] = None
        if request.attachment:
            info = self.transport.get_file(request.attachment.file_id)
            descriptor, name = tempfile.mkstemp(prefix=".incoming-", dir=self.store.root)
            os.close(descriptor)
            Path(name).unlink()
            temporary = Path(name)
            safe_name = sanitize_filename(request.attachment.file_name)
            self.transport.download_file(info["file_path"], temporary, request.attachment.file_size)
            payload = temporary.read_bytes()
            record["attachment"] = {
                "file_id": request.attachment.file_id,
                "file_name": safe_name,
                "mime_type": request.attachment.mime_type,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "path": f"files/{safe_name}",
            }
        try:
            return self.store.create(record, temporary)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def poll_once(self, timeout: int = 30) -> int:
        updates = self.transport.get_updates(self.store.offset, timeout)
        for update in updates:
            update_id = int(update["update_id"])
            request = parse_update(update, self.chat_id)
            if request is not None:
                item = self._save(request)
                try:
                    self.transport.confirm_saved(item["id"])
                except Exception:
                    pass
            self.store.set_offset(update_id + 1)
        return len(updates)

    def stop(self) -> None:
        self.stopped = True

    def run(self, max_cycles: Optional[int] = None) -> None:
        failures = 0
        cycles = 0
        while not self.stopped and (max_cycles is None or cycles < max_cycles):
            cycles += 1
            try:
                self.poll_once()
                failures = 0
            except Exception:
                delay = min(60, 2 ** failures)
                failures += 1
                self.sleeper(delay)
