from __future__ import annotations
import json, subprocess
from .config import Config

class TelegramError(RuntimeError): pass

class TelegramCurl:
    def __init__(self,config:Config): self.config=config
    def request(self,method:str,args:list[str])->dict:
        url=f"{self.config.telegram_api_base}/bot{self.config.bot_token}/{method}"
        curl_config=f'url = "{url}"\nsilent\nshow-error\nfail-with-body\nconnect-timeout = 15\nmax-time = 300\n'
        try:
            result=subprocess.run(["curl","--config","-",*args],input=curl_config,text=True,capture_output=True,timeout=310)
        except (OSError,subprocess.TimeoutExpired) as error:
            raise TelegramError("Telegram request could not be completed") from error
        if result.returncode:
            raise TelegramError(f"Telegram request failed (curl exit {result.returncode})")
        try: payload=json.loads(result.stdout)
        except json.JSONDecodeError as error: raise TelegramError("Telegram returned an invalid response") from error
        if not payload.get("ok"):
            description=str(payload.get("description","Telegram rejected the request")).replace(self.config.bot_token,"[redacted]")
            raise TelegramError(description)
        return payload["result"]
