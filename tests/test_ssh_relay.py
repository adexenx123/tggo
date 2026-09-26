import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from tggo.config import Config
from tggo.files import inspect_file
from tggo.planner import build_plan
from tggo.transports.ssh_relay import SSHRelayTransport


class Result:
    def __init__(self,code=0,out="",err=""): self.returncode=code; self.stdout=out; self.stderr=err

class RelayTests(unittest.TestCase):
    def config(self):
        return Config("ssh-relay","local-token-must-not-travel","123",ssh_host="relay.example",ssh_user="alice",ssh_port=2222,ssh_identity_file="/keys/id",remote_env_file="/home/alice/relay.env")

    def test_uses_separate_ssh_arguments_and_manifest_has_no_secret(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"a.txt"; path.write_text("hello"); files=[inspect_file(path,False,50)]
            calls=[]
            def fake(command,timeout=60):
                calls.append(command)
                if command[0]=="ssh" and "mktemp" in command[-1]: return Result(out="/tmp/tggo.ABC123\n")
                if command[0]=="scp" and command[-1].endswith("manifest.json"):
                    manifest=json.loads(Path(command[-2]).read_text())
                    self.assertNotIn("local-token-must-not-travel",json.dumps(manifest))
                    self.assertNotIn("chat_id",manifest)
                if command[0]=="ssh" and "tggo-relay.py" in command[-1]: return Result(out='{"status":"delivered","message_ids":[7]}')
                return Result()
            with patch("tggo.transports.ssh_relay.run",side_effect=fake):
                result=SSHRelayTransport(self.config()).send(build_plan("caption",files),files)
            self.assertEqual([7],result["message_ids"])
            self.assertIn("-p",calls[0]); self.assertIn("2222",calls[0]); self.assertIn("-i",calls[0])
            self.assertTrue(any("rm -rf -- /tmp/tggo.ABC123" in call[-1] for call in calls if call[0]=="ssh"))

    def test_rejects_unsafe_host(self):
        config=self.config(); config=Config(**{**config.__dict__,"ssh_host":"-oProxyCommand=bad"})
        with self.assertRaisesRegex(ValueError,"unsafe"): SSHRelayTransport(config)

    def test_doctor_uses_remote_runner(self):
        def fake(command,timeout=60):
            return Result(out='{"status":"ok","bot":"relay_bot"}')
        with patch("tggo.transports.ssh_relay.run",side_effect=fake):
            self.assertEqual("relay_bot",SSHRelayTransport(self.config()).doctor())
