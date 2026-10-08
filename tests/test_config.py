import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tggo.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def write(self, content: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "config.env"
        path.write_text(content, encoding="utf-8")
        os.chmod(path, 0o600)
        return path

    def test_loads_direct_mode(self):
        config = load_config(self.write("TGGO_MODE=direct\nTGGO_BOT_TOKEN=123:abc\nTGGO_CHAT_ID=456\n"))
        self.assertEqual("direct", config.mode)
        self.assertEqual(50, config.max_file_mb)
        self.assertEqual(Path("~/.local/share/tggo").expanduser(),config.data_dir)

    def test_loads_custom_data_directory_without_exposing_secrets(self):
        config=load_config(self.write("TGGO_MODE=direct\nTGGO_BOT_TOKEN=secret\nTGGO_CHAT_ID=456\nTGGO_DATA_DIR=/tmp/tggo-data\n"))
        self.assertEqual(Path("/tmp/tggo-data"),config.data_dir)
        self.assertNotIn("secret",repr(config.data_dir))

    def test_requires_relay_fields(self):
        path = self.write("TGGO_MODE=ssh-relay\nTGGO_BOT_TOKEN=123:abc\nTGGO_CHAT_ID=456\n")
        with self.assertRaisesRegex(ConfigError, "TGGO_SSH_HOST"):
            load_config(path)

    def test_relay_does_not_require_local_telegram_secret(self):
        path=self.write("TGGO_MODE=ssh-relay\nTGGO_SSH_HOST=relay.example\nTGGO_SSH_USER=alice\nTGGO_REMOTE_ENV_FILE=/home/alice/relay.env\n")
        config=load_config(path)
        self.assertEqual("",config.bot_token)
        self.assertEqual("",config.chat_id)

    def test_rejects_unknown_mode_and_bad_limits(self):
        for content in (
            "TGGO_MODE=other\nTGGO_BOT_TOKEN=123:abc\nTGGO_CHAT_ID=456\n",
            "TGGO_MODE=direct\nTGGO_BOT_TOKEN=123:abc\nTGGO_CHAT_ID=456\nTGGO_MAX_FILE_MB=0\n",
        ):
            with self.subTest(content=content):
                with self.assertRaises(ConfigError):
                    load_config(self.write(content))

    def test_error_never_contains_token(self):
        token = "123456:very-secret-token"
        with self.assertRaises(ConfigError) as caught:
            load_config(self.write(f"TGGO_MODE=bad\nTGGO_BOT_TOKEN={token}\nTGGO_CHAT_ID=1\n"))
        self.assertNotIn(token, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
