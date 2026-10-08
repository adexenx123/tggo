import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tggo.config import Config
from tggo.telegram import TelegramError
from tggo.transports.direct import DirectTransport
from tests.fake_telegram import FakeTelegram


class InboundTelegramTests(unittest.TestCase):
    def config(self, base, max_file_mb=1):
        return Config("direct", "123:secret", "99", max_file_mb=max_file_mb, telegram_api_base=base)

    def test_get_updates_get_file_download_and_confirmation(self):
        responses={"getUpdates":{"ok":True,"result":[{"update_id":4}]},"getFile":{"ok":True,"result":{"file_path":"docs/a.txt"}}}
        with tempfile.TemporaryDirectory() as directory, FakeTelegram(responses, {"a.txt":b"hello"}) as fake:
            transport=DirectTransport(self.config(fake.base))
            self.assertEqual(4,transport.get_updates(3,20)[0]["update_id"])
            info=transport.get_file("file-id")
            target=Path(directory)/"a.txt"
            transport.download_file(info["file_path"],target,5)
            self.assertEqual(b"hello",target.read_bytes())
            transport.confirm_saved("TG-ABC")
            self.assertTrue(any("sendMessage" in request[0] for request in fake.requests))

    def test_rejects_reported_oversize_before_download(self):
        with FakeTelegram() as fake:
            with self.assertRaises(TelegramError):
                DirectTransport(self.config(fake.base)).download_file("a",Path("unused"),2*1024*1024)
            self.assertEqual([],fake.requests)

    def test_malformed_json_and_errors_do_not_expose_token(self):
        with FakeTelegram({"getUpdates":b"not json"}) as fake:
            transport=DirectTransport(self.config(fake.base))
            with self.assertRaises(TelegramError) as caught: transport.get_updates(0,1)
            self.assertNotIn("123:secret",str(caught.exception))


if __name__ == "__main__": unittest.main()
