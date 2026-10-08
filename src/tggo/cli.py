from __future__ import annotations
import argparse, json, os, shutil, sys, uuid
from pathlib import Path
from .config import ConfigError, load_config
from .files import inspect_file
from .ledger import DuplicateRequest, Ledger
from .inbox import InboxStore
from .planner import build_plan
from .receiver import Receiver
from .transports.direct import DirectTransport
from .transports.ssh_relay import SSHRelayTransport

def config_path()->Path: return Path(os.environ.get("TGGO_CONFIG","~/.config/tggo/config.env")).expanduser()
def state_path()->Path: return Path(os.environ.get("TGGO_STATE_DIR","~/.local/state/tggo")).expanduser()
def transport(config): return DirectTransport(config) if config.mode=="direct" else SSHRelayTransport(config)

def add_payload(parser):
    parser.add_argument("--text",default=""); parser.add_argument("--file",action="append",default=[]); parser.add_argument("--allow-sensitive",action="store_true")

def parser()->argparse.ArgumentParser:
    root=argparse.ArgumentParser(prog="tggo"); commands=root.add_subparsers(dest="command",required=True)
    send=commands.add_parser("send"); add_payload(send); send.add_argument("--request-id")
    preview=commands.add_parser("preview"); add_payload(preview)
    commands.add_parser("doctor"); commands.add_parser("test")
    config=commands.add_parser("config"); config.add_argument("--set",required=True,metavar="KEY=VALUE")
    inbox=commands.add_parser("inbox"); inbox.add_argument("action",nargs="?",choices=["show","download","read","archive"]); inbox.add_argument("identifier",nargs="?"); inbox.add_argument("--output"); inbox.add_argument("--json",action="store_true"); inbox.add_argument("--all",action="store_true")
    listen=commands.add_parser("inbox-listen"); listen.add_argument("--once",action="store_true")
    return root

def payload(args,config):
    text=args.text
    if not text and not args.file and not sys.stdin.isatty(): text=sys.stdin.read()
    if not text.strip() and not args.file: raise ValueError("provide --text, stdin, or at least one --file")
    files=[inspect_file(Path(item),args.allow_sensitive,config.max_file_mb) for item in args.file]
    if sum(item.size for item in files)>config.max_total_mb*1024*1024: raise ValueError("total attachment size is too large")
    return text,files,build_plan(text,files)

def update_config(spec:str)->None:
    if "=" not in spec: raise ValueError("--set requires KEY=VALUE")
    key,value=spec.split("=",1)
    allowed={"TGGO_MODE","TGGO_CHAT_ID","TGGO_MAX_FILE_MB","TGGO_MAX_TOTAL_MB","TGGO_TELEGRAM_API_BASE","TGGO_SSH_HOST","TGGO_SSH_USER","TGGO_SSH_PORT","TGGO_SSH_IDENTITY_FILE","TGGO_REMOTE_ENV_FILE","TGGO_DATA_DIR"}
    if key not in allowed: raise ValueError(f"{key} cannot be changed with this command")
    path=config_path(); lines=path.read_text(encoding="utf-8").splitlines(); found=False; output=[]
    for line in lines:
        if line.startswith(key+"="): output.append(f"{key}={value}"); found=True
        else: output.append(line)
    if not found: output.append(f"{key}={value}")
    path.write_text("\n".join(output)+"\n",encoding="utf-8"); os.chmod(path,0o600)

def main(argv:list[str]|None=None)->int:
    args=parser().parse_args(argv)
    try:
        if args.command=="config": update_config(args.set); print("Configuration updated"); return 0
        config=load_config(config_path()); channel=transport(config)
        if args.command=="inbox-listen":
            if config.mode!="direct": raise ValueError("inbox-listen must run on the SSH relay host")
            receiver=Receiver(InboxStore(config.data_dir/"inbox"),channel,config.chat_id)
            if args.once: receiver.poll_once()
            else: receiver.run()
            return 0
        if args.command=="inbox":
            if config.mode=="ssh-relay":
                result=channel.inbox(args.action or "list",args.identifier,args.output,args.all)
                if result is not None: print(json.dumps(result,ensure_ascii=False,indent=2) if args.json or isinstance(result,(dict,list)) else result)
                return 0
            store=InboxStore(config.data_dir/"inbox")
            action=args.action or "list"
            if action=="list": result=store.list(include_archived=args.all)
            else:
                if not args.identifier: raise ValueError(f"inbox {action} requires an ID")
                if action=="show": result=store.get(args.identifier)
                elif action=="read": result=store.mark_read(args.identifier)
                elif action=="archive": result=store.archive(args.identifier)
                else:
                    item=store.get(args.identifier); attachment=item.get("attachment")
                    if not attachment: raise ValueError("inbox item has no attachment")
                    source=store.root/item["id"]/attachment["path"]
                    destination=Path(args.output or attachment["file_name"]).expanduser()
                    if destination.exists(): raise ValueError(f"output already exists: {destination}")
                    shutil.copyfile(source,destination); os.chmod(destination,0o600); result=str(destination)
            if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
            elif isinstance(result,list):
                for item in result: print(f"{item['id']} {'archived' if item['archived'] else 'unread' if not item['read'] else 'read'} {item.get('text','')}")
            elif isinstance(result,dict): print(json.dumps(result,ensure_ascii=False,indent=2))
            else: print(result)
            return 0
        if args.command=="doctor": print(f"OK: @{channel.doctor()}"); return 0
        if args.command=="test":
            result=channel.send(build_plan("TGGO connection test",[]),[]); print(json.dumps(result)); return 0
        text,files,plan=payload(args,config)
        if args.command=="preview":
            result={"status":"preview","files":[{"name":f.name,"size":f.size,"mime":f.mime,"sha256":f.sha256} for f in files],"plan":plan}
            print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
        request_id=args.request_id or str(uuid.uuid4()); ledger=Ledger(state_path()/"ledger.json")
        try: ledger.begin(request_id,[file.sha256 for file in files])
        except DuplicateRequest as error: print(str(error),file=sys.stderr); return 3
        try: result=channel.send(plan,files)
        except Exception as error:
            ledger.unknown(request_id,str(error)); print(f"delivery result is uncertain; not retrying: {error}",file=sys.stderr); return 2
        result["request_id"]=request_id; result["files"]=[{"name":f.name,"size":f.size,"sha256":f.sha256} for f in files]
        ledger.finish(request_id,result); print(json.dumps(result,ensure_ascii=False)); return 0
    except (ConfigError,ValueError,OSError) as error:
        print(f"error: {error}",file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
