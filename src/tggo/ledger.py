from __future__ import annotations
import json, os
from pathlib import Path

class DuplicateRequest(RuntimeError): pass

class Ledger:
    def __init__(self,path:Path): self.path=path
    def _load(self)->dict:
        try: data=json.loads(self.path.read_text(encoding="utf-8")); return data if isinstance(data,dict) else {}
        except FileNotFoundError: return {}
    def _save(self,data:dict)->None:
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        temp=self.path.with_suffix(".tmp"); temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
        os.chmod(temp,0o600); temp.replace(self.path)
    def get(self,request_id:str): return self._load().get(request_id)
    def begin(self,request_id:str,hashes:list[str])->None:
        data=self._load()
        if request_id in data: raise DuplicateRequest(f"request {request_id} already exists")
        data[request_id]={"status":"pending","files":hashes}; self._save(data)
    def finish(self,request_id:str,result:dict)->None:
        data=self._load(); data[request_id]=result; self._save(data)
    def unknown(self,request_id:str,error:str)->None:
        data=self._load(); data[request_id]={"status":"unknown","error":error[:500]}; self._save(data)
