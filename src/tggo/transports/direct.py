from __future__ import annotations
import json
from pathlib import Path
from ..config import Config
from ..files import FileInfo
from ..telegram import TelegramCurl, TelegramError

class DirectTransport:
    def __init__(self,config:Config): self.config=config; self.client=TelegramCurl(config)
    def doctor(self)->str:
        result=self.client.request("getMe",[])
        return str(result.get("username") or result.get("first_name") or "Telegram bot")
    def get_updates(self,offset:int,timeout:int=30)->list[dict]:
        result=self.client.request("getUpdates",["--form-string",f"offset={offset}","--form-string",f"timeout={timeout}","--form-string","allowed_updates=[\"message\"]"])
        if not isinstance(result,list): raise TelegramError("Telegram updates response is invalid")
        return result
    def get_file(self,file_id:str)->dict:
        result=self.client.request("getFile",["--form-string",f"file_id={file_id}"])
        if not isinstance(result,dict) or not result.get("file_path"): raise TelegramError("Telegram file response is invalid")
        return result
    def download_file(self,file_path:str,target:Path,reported_size:int)->Path:
        limit=self.config.max_file_mb*1024*1024
        if reported_size>limit: raise TelegramError("Telegram file exceeds configured size limit")
        target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        return self.client.download(file_path,target,limit)
    def confirm_saved(self,identifier:str)->None:
        self.client.request("sendMessage",["--form-string",f"chat_id={self.config.chat_id}","--form-string",f"text=✅ 已存入 TGGO 收件匣｜編號 {identifier}"])
    def confirm_failed(self)->None:
        self.client.request("sendMessage",["--form-string",f"chat_id={self.config.chat_id}","--form-string","text=⚠️ TGGO 收件匣保存失敗，稍後將重試"])
    def _ids(self,result)->list[int]:
        messages=result if isinstance(result,list) else [result]
        return [int(message["message_id"]) for message in messages if isinstance(message,dict) and "message_id" in message]
    def send(self,plan:list[dict[str,object]],files:list[FileInfo])->dict[str,object]:
        ids=[]
        for item in plan:
            kind=item["kind"]
            if kind=="text":
                result=self.client.request("sendMessage",["--form-string",f"chat_id={self.config.chat_id}","--form-string",f"text={item['text']}","--form-string","disable_web_page_preview=true"])
            elif kind=="file":
                file=files[int(item["file_index"])]; field=str(item["method"]); method="send"+field[0].upper()+field[1:]
                args=["--form-string",f"chat_id={self.config.chat_id}"]
                if item.get("caption"): args.extend(["--form-string",f"caption={item['caption']}"])
                args.extend(["-F",f"{field}=@{file.path};type={file.mime};filename={file.name}"])
                result=self.client.request(method,args)
            else:
                args=["--form-string",f"chat_id={self.config.chat_id}"]; media=[]
                for position,index in enumerate(item["file_indexes"]):
                    file=files[int(index)]; key=f"attach{position}"
                    args.extend(["-F",f"{key}=@{file.path};type={file.mime};filename={file.name}"])
                    entry={"type":file.media_type,"media":f"attach://{key}"}
                    if position==0 and item.get("caption"): entry["caption"]=item["caption"]
                    media.append(entry)
                args.extend(["--form-string",f"media={json.dumps(media,ensure_ascii=False)}"])
                result=self.client.request("sendMediaGroup",args)
            ids.extend(self._ids(result))
        return {"status":"delivered","message_ids":ids}

__all__=["DirectTransport","TelegramError"]
