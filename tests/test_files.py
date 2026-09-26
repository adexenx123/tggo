import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from tggo.files import inspect_file, classify_file, sanitize_filename


class FileTests(unittest.TestCase):
    def test_classifies_media(self):
        expected={"a.jpg":"photo","a.mp4":"video","a.mp3":"audio","a.ogg":"voice","a.gif":"animation","a.pdf":"document"}
        for name,kind in expected.items(): self.assertEqual(kind,classify_file(Path(name)))

    def test_rejects_symlink_sensitive_and_large(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=root/"a.txt"; target.write_text("x"); link=root/"link.txt"; link.symlink_to(target)
            with self.assertRaisesRegex(ValueError,"symbolic"): inspect_file(link,False,50)
            secret=root/".env"; secret.write_text("TOKEN=x")
            with self.assertRaisesRegex(ValueError,"sensitive"): inspect_file(secret,False,50)
            large=root/"large.bin"; large.write_bytes(b"xx")
            with self.assertRaisesRegex(ValueError,"too large"): inspect_file(large,False,0.000001)

    def test_hash_and_sanitized_name(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bad name?.txt"; path.write_text("hello")
            info=inspect_file(path,False,50)
            self.assertEqual("bad_name_.txt",info.name)
            self.assertEqual(64,len(info.sha256))
            self.assertEqual("evil_.pdf",sanitize_filename("../evil?.pdf"))
