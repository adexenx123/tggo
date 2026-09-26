#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"src"))
sys.path.insert(0,str(HERE.parent/"src"))
from tggo.config import load_config
from tggo.files import FileInfo
from tggo.transports.direct import DirectTransport

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument("--manifest"); parser.add_argument("--env",required=True); parser.add_argument("--preview",action="store_true"); parser.add_argument("--doctor",action="store_true")
    args=parser.parse_args(); config=load_config(Path(args.env).expanduser())
    if args.doctor:
        print(json.dumps({"status":"ok","bot":DirectTransport(config).doctor()})); return 0
    if not args.manifest: parser.error("--manifest is required unless --doctor is used")
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if args.preview:
        print(json.dumps({"status":"preview","configured_chat":config.chat_id,"files":len(manifest.get("files",[]))})); return 0
    files=[FileInfo(Path(item["path"]),item["name"],int(item["size"]),item["mime"],item["media_type"],item["sha256"]) for item in manifest.get("files",[])]
    result=DirectTransport(config).send(manifest.get("plan",[]),files); print(json.dumps(result)); return 0

if __name__=="__main__": raise SystemExit(main())
