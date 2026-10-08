import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tggo.inbox import InboxStore
from tggo.receiver import Receiver


class FakeTransport:
    def __init__(self, updates, fail_confirmation=False):
        self.updates=updates; self.confirmed=[]; self.fail_confirmation=fail_confirmation
    def get_updates(self,offset,timeout=30): return [item for item in self.updates if item["update_id"]>=offset]
    def get_file(self,file_id): return {"file_path":"docs/file.bin"}
    def download_file(self,file_path,target,reported_size): target.write_bytes(b"payload"); return target
    def confirm_saved(self,identifier):
        self.confirmed.append(identifier)
        if self.fail_confirmation: raise RuntimeError("offline")
    def confirm_failed(self): pass


def message(update_id,text="/tggo hello",chat=99,attachment=False):
    body={"message_id":update_id,"chat":{"id":chat}}
    if attachment: body.update({"caption":text,"document":{"file_id":"f","file_name":"../a.bin","file_size":7}})
    else: body["text"]=text
    return {"update_id":update_id,"message":body}


class ReceiverTests(unittest.TestCase):
    def test_saves_authorized_ignores_other_and_advances_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            store=InboxStore(Path(directory)/"inbox"); transport=FakeTransport([message(1),message(2,"hello"),message(3,chat=88)])
            Receiver(store,transport,"99").poll_once()
            self.assertEqual(1,len(store.list())); self.assertEqual(4,store.offset); self.assertEqual(1,len(transport.confirmed))

    def test_attachment_hash_and_safe_name(self):
        with tempfile.TemporaryDirectory() as directory:
            store=InboxStore(Path(directory)/"inbox")
            Receiver(store,FakeTransport([message(5,attachment=True)]),"99").poll_once()
            item=store.list()[0]; attachment=item["attachment"]
            self.assertEqual(hashlib.sha256(b"payload").hexdigest(),attachment["sha256"])
            self.assertEqual(b"payload",(store.root/item["id"] / attachment["path"]).read_bytes())
            self.assertNotIn("..",attachment["path"])

    def test_duplicate_and_confirmation_failure_do_not_duplicate_or_rewind(self):
        with tempfile.TemporaryDirectory() as directory:
            store=InboxStore(Path(directory)/"inbox"); transport=FakeTransport([message(7)],True); receiver=Receiver(store,transport,"99")
            receiver.poll_once(); store.set_offset(7); receiver.poll_once()
            self.assertEqual(1,len(store.list())); self.assertEqual(8,store.offset)

    def test_loop_uses_bounded_backoff_and_stops(self):
        sleeps=[]
        class Broken:
            def get_updates(self,*args,**kwargs): raise RuntimeError("down")
        with tempfile.TemporaryDirectory() as directory:
            receiver=Receiver(InboxStore(Path(directory)/"inbox"),Broken(),"99",sleeper=lambda seconds:sleeps.append(seconds))
            receiver.run(max_cycles=5)
        self.assertEqual([1,2,4,8,16],sleeps)


if __name__ == "__main__": unittest.main()
