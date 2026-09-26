from __future__ import annotations
import hashlib, mimetypes, re
from pathlib import Path
from typing import NamedTuple

SENSITIVE_NAMES={".env",".env.local","id_rsa","id_ed25519","credentials.json"}
SENSITIVE_SUFFIXES={".key",".pem",".p12",".pfx",".kdbx"}

class FileInfo(NamedTuple):
    path: Path; name: str; size: int; mime: str; media_type: str; sha256: str

def sanitize_filename(filename:str)->str:
    cleaned=re.sub(r"[^A-Za-z0-9._()\-\u4e00-\u9fff]","_",Path(filename).name)
    return (cleaned.lstrip(".") or "file")[:180]

def classify_file(path:Path)->str:
    suffix=path.suffix.lower()
    if suffix in {".jpg",".jpeg",".png",".webp"}: return "photo"
    if suffix==".mp4": return "video"
    if suffix in {".mp3",".m4a",".flac",".wav"}: return "audio"
    if suffix in {".ogg",".oga",".opus"}: return "voice"
    if suffix==".gif": return "animation"
    return "document"

def _hash(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()

def inspect_file(path:Path,allow_sensitive:bool,max_file_mb:float)->FileInfo:
    path=path.expanduser()
    if path.is_symlink(): raise ValueError(f"symbolic link is not allowed: {path}")
    if not path.exists(): raise ValueError(f"file does not exist: {path}")
    if not path.is_file(): raise ValueError(f"not a regular file: {path}")
    if path.stat().st_size>max_file_mb*1024*1024: raise ValueError(f"file is too large: {path}")
    name=path.name.lower()
    sensitive=name in SENSITIVE_NAMES or path.suffix.lower() in SENSITIVE_SUFFIXES or "credential" in name or "secret" in name
    if sensitive and not allow_sensitive: raise ValueError(f"sensitive file requires explicit confirmation: {path.name}")
    return FileInfo(path.resolve(),sanitize_filename(path.name),path.stat().st_size,
                    mimetypes.guess_type(path.name)[0] or "application/octet-stream",classify_file(path),_hash(path))
