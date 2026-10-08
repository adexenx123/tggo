import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tggo.inbox import InboxStore


class InboxStoreTests(unittest.TestCase):
    def test_create_deduplicate_and_persist_atomic_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "inbox"
            store = InboxStore(root)
            item = store.create({"update_id": 7, "message_id": 8, "chat_id": "9", "text": "hello"})
            self.assertRegex(item["id"], r"^TG-[0-9A-F]{12}$")
            self.assertEqual(item["id"], store.create({"update_id": 7})["id"])
            self.assertEqual("hello", InboxStore(root).get(item["id"])["text"])
            self.assertFalse((root / "index.json.tmp").exists())

    def test_record_is_immutable_while_state_changes_live_in_index(self):
        with tempfile.TemporaryDirectory() as directory:
            store = InboxStore(Path(directory) / "inbox")
            item = store.create({"update_id": 1, "text": "data"})
            record_path = store.root / item["id"] / "record.json"
            original = record_path.read_bytes()
            store.mark_read(item["id"])
            store.archive(item["id"])
            current = store.get(item["id"])
            self.assertTrue(current["read"])
            self.assertTrue(current["archived"])
            self.assertEqual(original, record_path.read_bytes())

    def test_permissions_are_private(self):
        with tempfile.TemporaryDirectory() as directory:
            store = InboxStore(Path(directory) / "inbox")
            item = store.create({"update_id": 2})
            self.assertEqual(0o700, os.stat(store.root).st_mode & 0o777)
            self.assertEqual(0o600, os.stat(store.root / "index.json").st_mode & 0o777)
            self.assertEqual(0o600, os.stat(store.root / item["id"] / "record.json").st_mode & 0o777)

    def test_list_hides_archived_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            store = InboxStore(Path(directory) / "inbox")
            item = store.create({"update_id": 3})
            store.archive(item["id"])
            self.assertEqual([], store.list())
            self.assertEqual(1, len(store.list(include_archived=True)))


if __name__ == "__main__":
    unittest.main()
