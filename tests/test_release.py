import re, subprocess, unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]

class ReleaseTests(unittest.TestCase):
    def test_required_public_docs_and_scanner_exist(self):
        for relative in ("README.md","SECURITY.md","scripts/check-release.sh"):
            self.assertTrue((ROOT/relative).is_file(),relative)

    def test_example_contains_no_real_credentials(self):
        example=(ROOT/".env.example").read_text(encoding="utf-8")
        self.assertRegex(example,r"(?m)^TGGO_BOT_TOKEN=$")
        self.assertRegex(example,r"(?m)^TGGO_CHAT_ID=$")

    def test_tracked_files_and_history_have_no_private_markers(self):
        files=subprocess.run(["git","ls-files"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.splitlines()
        content="\n".join((ROOT/name).read_text(encoding="utf-8",errors="ignore") for name in files)
        private_ip="45.76."+"204.24"
        self.assertNotIn(private_ip,content)
        self.assertIsNone(re.search(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b",content))
        forbidden=[name for name in files if name.endswith("/.env") or "ledger.json" in name or name.lower().endswith((".jpg",".png",".zip"))]
        self.assertEqual([],forbidden)

    def test_readme_documents_both_modes_and_installation(self):
        readme=(ROOT/"README.md").read_text(encoding="utf-8")
        for phrase in ("direct","ssh-relay","install.sh","TGGO_BOT_TOKEN","$tggo"):
            self.assertIn(phrase,readme)

if __name__=="__main__": unittest.main()
