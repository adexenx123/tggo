from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class InboundAttachment:
    file_id: str
    file_name: str
    mime_type: str
    file_size: int
    kind: str


@dataclass(frozen=True)
class InboundRequest:
    update_id: int
    message_id: int
    chat_id: str
    text: str
    attachment: Optional[InboundAttachment]


PREFIX = re.compile(r"^\s*/tggo(?:@[A-Za-z0-9_]+)?(?:\s+|$)", re.IGNORECASE)


def _attachment(message: dict[str, Any]) -> Optional[InboundAttachment]:
    kind = ""
    source: Optional[dict[str, Any]] = None
    if isinstance(message.get("photo"), list) and message["photo"]:
        kind = "photo"
        source = max(message["photo"], key=lambda item: int(item.get("file_size", 0)))
    else:
        for candidate in ("document", "video", "audio", "voice", "animation"):
            if isinstance(message.get(candidate), dict):
                kind, source = candidate, message[candidate]
                break
    if source is None:
        return None
    return InboundAttachment(
        file_id=str(source["file_id"]),
        file_name=str(source.get("file_name") or f"{kind}-{source['file_id']}"),
        mime_type=str(source.get("mime_type") or "application/octet-stream"),
        file_size=int(source.get("file_size") or 0),
        kind=kind,
    )


def parse_update(update: dict[str, Any], allowed_chat_id: str) -> Optional[InboundRequest]:
    message = update.get("message")
    if not isinstance(message, dict) or str(message.get("chat", {}).get("id")) != str(allowed_chat_id):
        return None
    attachment = _attachment(message)
    raw = message.get("caption") if attachment else message.get("text")
    if not isinstance(raw, str):
        return None
    match = PREFIX.match(raw)
    if not match:
        return None
    return InboundRequest(
        update_id=int(update["update_id"]),
        message_id=int(message["message_id"]),
        chat_id=str(message["chat"]["id"]),
        text=raw[match.end():].strip(),
        attachment=attachment,
    )
