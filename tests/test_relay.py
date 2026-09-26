import json, subprocess, sys, tempfile, unittest
from pathlib import Path


class RelayRunnerTests(unittest.TestCase):
    def test_manifest_cannot_override_destination(self):
        source=Path(__file__).parents[1]/"relay"/"tggo-relay.py"
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manifest=root/"manifest.json"; env=root/"relay.env"
            manifest.write_text(json.dumps({"chat_id":"attacker","bot_token":"attacker","files":[],"plan":[]}),encoding="utf-8")
            env.write_text("TGGO_BOT_TOKEN=real\nTGGO_CHAT_ID=owner\nTGGO_TELEGRAM_API_BASE=http://127.0.0.1:1\n",encoding="utf-8")
            result=subprocess.run([sys.executable,str(source),"--manifest",str(manifest),"--env",str(env),"--preview"],capture_output=True,text=True)
            self.assertEqual(0,result.returncode,result.stderr)
            output=json.loads(result.stdout)
            self.assertEqual("owner",output["configured_chat"])
            self.assertNotIn("real",result.stdout)
