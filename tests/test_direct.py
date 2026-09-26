import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from tggo.config import Config
from tggo.files import inspect_file
from tggo.planner import build_plan
from tggo.transports.direct import DirectTransport, TelegramError
from tests.fake_telegram import FakeTelegram


class DirectTests(unittest.TestCase):
    def config(self,base): return Config("direct","123:secret","999",telegram_api_base=base)
    def test_doctor_and_text_return_message_id(self):
        with FakeTelegram() as fake:
            transport=DirectTransport(self.config(fake.base))
            self.assertEqual("fake_bot",transport.doctor())
            result=transport.send(build_plan("hello",[]),[])
            self.assertEqual([42],result["message_ids"])
            self.assertIn("/bot123:secret/getMe",fake.requests[0][0])
            self.assertIn(b"hello",fake.requests[1][2])

    def test_uploads_document_and_album_as_multipart(self):
        with tempfile.TemporaryDirectory() as d, FakeTelegram() as fake:
            root=Path(d); pdf=root/"report.pdf"; pdf.write_bytes(b"pdf")
            a=root/"a.jpg"; b=root/"b.jpg"; a.write_bytes(b"aaa"); b.write_bytes(b"bbb")
            transport=DirectTransport(self.config(fake.base))
            one=[inspect_file(pdf,False,50)]; transport.send(build_plan("caption",one),one)
            photos=[inspect_file(a,False,50),inspect_file(b,False,50)]; transport.send(build_plan("album",photos),photos)
            self.assertIn("sendDocument",fake.requests[0][0]); self.assertIn(b"report.pdf",fake.requests[0][2])
            self.assertIn("sendMediaGroup",fake.requests[1][0]); self.assertIn(b"attach://attach0",fake.requests[1][2])

    def test_redacts_token_from_connection_error(self):
        config=self.config("http://127.0.0.1:1")
        with self.assertRaises(TelegramError) as caught: DirectTransport(config).doctor()
        self.assertNotIn(config.bot_token,str(caught.exception))


if __name__=="__main__": unittest.main()
