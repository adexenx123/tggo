from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    mode: str
    bot_token: str
    chat_id: str
    max_file_mb: int = 50
    max_total_mb: int = 200
    telegram_api_base: str = "https://api.telegram.org"
    ssh_host: str = ""
    ssh_user: str = ""
    ssh_port: int = 22
    ssh_identity_file: str = ""
    remote_env_file: str = ""
    data_dir: Path = Path("~/.local/share/tggo").expanduser()


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"invalid configuration line {number}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _positive(values: dict[str, str], key: str, default: int) -> int:
    try:
        result = int(values.get(key, str(default)))
    except ValueError as error:
        raise ConfigError(f"{key} must be a positive integer") from error
    if result <= 0:
        raise ConfigError(f"{key} must be a positive integer")
    return result


def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"configuration file not found: {path}")
    values = _parse_env(path)
    mode = values.get("TGGO_MODE", "direct")
    if mode not in {"direct", "ssh-relay"}:
        raise ConfigError("TGGO_MODE must be direct or ssh-relay")
    missing = []
    if mode == "direct":
        missing.extend(key for key in ("TGGO_BOT_TOKEN", "TGGO_CHAT_ID") if not values.get(key))
    else:
        missing.extend(key for key in ("TGGO_SSH_HOST", "TGGO_SSH_USER", "TGGO_REMOTE_ENV_FILE") if not values.get(key))
    if missing:
        raise ConfigError("missing configuration: " + ", ".join(missing))
    return Config(
        mode=mode,
        bot_token=values.get("TGGO_BOT_TOKEN", ""),
        chat_id=values.get("TGGO_CHAT_ID", ""),
        max_file_mb=_positive(values, "TGGO_MAX_FILE_MB", 50),
        max_total_mb=_positive(values, "TGGO_MAX_TOTAL_MB", 200),
        telegram_api_base=values.get("TGGO_TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/"),
        ssh_host=values.get("TGGO_SSH_HOST", ""),
        ssh_user=values.get("TGGO_SSH_USER", ""),
        ssh_port=_positive(values, "TGGO_SSH_PORT", 22),
        ssh_identity_file=values.get("TGGO_SSH_IDENTITY_FILE", ""),
        remote_env_file=values.get("TGGO_REMOTE_ENV_FILE", ""),
        data_dir=Path(os.environ.get("TGGO_DATA_DIR",values.get("TGGO_DATA_DIR","~/.local/share/tggo"))).expanduser(),
    )
