from __future__ import annotations
import json, re, shlex, subprocess, tempfile
from pathlib import Path
from ..config import Config
from ..files import FileInfo

def run(command:list[str],timeout:int=60)->subprocess.CompletedProcess[str]:
    return subprocess.run(command,check=False,capture_output=True,text=True,timeout=timeout)

class SSHRelayTransport:
    def __init__(self,config:Config):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*",config.ssh_host) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*",config.ssh_user):
            raise ValueError("unsafe SSH host or user")
        self.config=config; self.destination=f"{config.ssh_user}@{config.ssh_host}"
    def _ssh_base(self)->list[str]:
        args=["ssh","-p",str(self.config.ssh_port)]
        if self.config.ssh_identity_file: args.extend(["-i",self.config.ssh_identity_file])
        return [*args,self.destination]
    def _scp_base(self)->list[str]:
        args=["scp","-q","-P",str(self.config.ssh_port)]
        if self.config.ssh_identity_file: args.extend(["-i",self.config.ssh_identity_file])
        return args
    def doctor(self)->str:
        command="python3 ~/.local/lib/tggo-relay/tggo-relay.py --doctor --env "+shlex.quote(self.config.remote_env_file)
        checked=run([*self._ssh_base(),command],30)
        if checked.returncode: raise RuntimeError("relay doctor failed")
        return str(json.loads(checked.stdout)["bot"])
    def send(self,plan:list[dict[str,object]],files:list[FileInfo])->dict[str,object]:
        made=run([*self._ssh_base(),"mktemp -d /tmp/tggo.XXXXXXXX"],15)
        if made.returncode: raise RuntimeError("could not create relay staging directory")
        remote_dir=made.stdout.strip()
        if not re.fullmatch(r"/tmp/tggo\.[A-Za-z0-9]+",remote_dir): raise RuntimeError("relay returned an unsafe staging path")
        try:
            manifest_files=[]
            for index,file in enumerate(files):
                remote_path=f"{remote_dir}/{index:03d}-{file.name}"
                copied=run([*self._scp_base(),"--",str(file.path),f"{self.destination}:{remote_path}"],120)
                if copied.returncode: raise RuntimeError(f"could not stage {file.name}")
                manifest_files.append({"path":remote_path,"name":file.name,"size":file.size,"mime":file.mime,"media_type":file.media_type,"sha256":file.sha256})
            manifest={"files":manifest_files,"plan":plan}
            with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False,suffix=".json") as handle:
                json.dump(manifest,handle,ensure_ascii=False); local=Path(handle.name)
            try:
                copied=run([*self._scp_base(),"--",str(local),f"{self.destination}:{remote_dir}/manifest.json"],30)
                if copied.returncode: raise RuntimeError("could not stage relay manifest")
            finally: local.unlink(missing_ok=True)
            command=("python3 ~/.local/lib/tggo-relay/tggo-relay.py --manifest "+shlex.quote(remote_dir+"/manifest.json")+
                     " --env "+shlex.quote(self.config.remote_env_file))
            sent=run([*self._ssh_base(),command],310)
            if sent.returncode: raise RuntimeError("relay delivery failed with an uncertain result")
            return json.loads(sent.stdout)
        finally:
            run([*self._ssh_base(),"rm -rf -- "+shlex.quote(remote_dir)],20)
