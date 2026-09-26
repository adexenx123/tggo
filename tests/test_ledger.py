import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from tggo.ledger import Ledger, DuplicateRequest


class LedgerTests(unittest.TestCase):
    def test_blocks_duplicate_and_records_state(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Ledger(Path(d)/"ledger.json")
            ledger.begin("id-1",["hash"])
            self.assertEqual("pending",ledger.get("id-1")["status"])
            with self.assertRaises(DuplicateRequest): ledger.begin("id-1",[])
            ledger.finish("id-1",{"status":"delivered","message_ids":[1]})
            self.assertEqual("delivered",ledger.get("id-1")["status"])
            self.assertEqual(0o600,(Path(d)/"ledger.json").stat().st_mode & 0o777)

    def test_unknown_is_not_retried(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Ledger(Path(d)/"ledger.json"); ledger.begin("id-2",[]); ledger.unknown("id-2","timeout")
            with self.assertRaises(DuplicateRequest): ledger.begin("id-2",[])
