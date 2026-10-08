import contextlib, io, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from tggo.cli import main
from tests.fake_telegram import FakeTelegram


class CLITests(unittest.TestCase):
    def setup_env(self,root:Path,base:str):
        config=root/"config.env"
        config.write_text(f"TGGO_MODE=direct\nTGGO_BOT_TOKEN=123:secret\nTGGO_CHAT_ID=9\nTGGO_TELEGRAM_API_BASE={base}\n",encoding="utf-8")
        os.chmod(config,0o600); os.environ["TGGO_CONFIG"]=str(config); os.environ["TGGO_STATE_DIR"]=str(root/"state"); os.environ["TGGO_DATA_DIR"]=str(root/"data")

    def tearDown(self):
        os.environ.pop("TGGO_CONFIG",None); os.environ.pop("TGGO_STATE_DIR",None); os.environ.pop("TGGO_DATA_DIR",None)

    def test_inbox_list_show_download_read_archive_and_json(self):
        from tggo.inbox import InboxStore
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.setup_env(root,"http://127.0.0.1:1"); store=InboxStore(root/"data"/"inbox")
            source=root/"source"; source.write_bytes(b"file")
            item=store.create({"update_id":1,"text":"hello","attachment":{"path":"files/a.txt","file_name":"a.txt","sha256":"x","size":4}},source)
            output=io.StringIO()
            with contextlib.redirect_stdout(output): self.assertEqual(0,main(["inbox","--json"]))
            self.assertIn(item["id"],output.getvalue())
            self.assertEqual(0,main(["inbox","show",item["id"]]))
            destination=root/"copy.txt"; self.assertEqual(0,main(["inbox","download",item["id"],"--output",str(destination)])); self.assertEqual(b"file",destination.read_bytes())
            self.assertEqual(0,main(["inbox","read",item["id"]])); self.assertTrue(store.get(item["id"])["read"])
            self.assertEqual(0,main(["inbox","archive",item["id"]])); self.assertTrue(store.get(item["id"])["archived"])

    def test_inbox_listen_runs_receiver(self):
        with tempfile.TemporaryDirectory() as d, FakeTelegram({"getUpdates":{"ok":True,"result":[]}}) as fake:
            self.setup_env(Path(d),fake.base)
            self.assertEqual(0,main(["inbox-listen","--once"]))

    def test_preview_does_not_create_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.setup_env(root,"http://127.0.0.1:1"); output=io.StringIO()
            with contextlib.redirect_stdout(output): code=main(["preview","--text","hello"])
            self.assertEqual(0,code); self.assertIn('"status": "preview"',output.getvalue()); self.assertFalse((root/"state"/"ledger.json").exists())

    def test_send_records_message_and_blocks_duplicate(self):
        with tempfile.TemporaryDirectory() as d, FakeTelegram() as fake:
            root=Path(d); self.setup_env(root,fake.base)
            self.assertEqual(0,main(["send","--text","hello","--request-id","same-id"]))
            self.assertEqual(3,main(["send","--text","hello","--request-id","same-id"]))

    def test_doctor_and_explicit_test(self):
        with tempfile.TemporaryDirectory() as d, FakeTelegram() as fake:
            self.setup_env(Path(d),fake.base)
            self.assertEqual(0,main(["doctor"])); self.assertEqual(0,main(["test"]))
            self.assertTrue(any(b"TGGO connection test" in request[2] for request in fake.requests))

    def test_config_updates_one_allowed_value(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.setup_env(root,"http://127.0.0.1:1")
            self.assertEqual(0,main(["config","--set","TGGO_MAX_FILE_MB=25"]))
            self.assertIn("TGGO_MAX_FILE_MB=25",Path(os.environ["TGGO_CONFIG"]).read_text())


if __name__=="__main__": unittest.main()
