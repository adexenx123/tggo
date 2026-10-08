import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from tggo.inbound import parse_update


class InboundParserTests(unittest.TestCase):
    def message(self, text=None, caption=None, chat=99, **extra):
        message = {"message_id": 4, "chat": {"id": chat}, **extra}
        if text is not None:
            message["text"] = text
        if caption is not None:
            message["caption"] = caption
        return {"update_id": 3, "message": message}

    def test_parses_text_and_bot_suffix_without_interpreting_body(self):
        for text, expected in [("/tggo hello", "hello"), ("  /tggo@my_bot   rm -rf /  ", "rm -rf /")]:
            with self.subTest(text=text):
                request = parse_update(self.message(text=text), "99")
                self.assertEqual(expected, request.text)
                self.assertIsNone(request.attachment)

    def test_parses_captioned_document(self):
        update = self.message(caption="/tggo receipt", document={"file_id": "abc", "file_name": "../bill.pdf", "mime_type": "application/pdf", "file_size": 12})
        request = parse_update(update, "99")
        self.assertEqual("receipt", request.text)
        self.assertEqual("abc", request.attachment.file_id)

    def test_chooses_largest_photo(self):
        update = self.message(caption="/tggo image", photo=[{"file_id": "small", "file_size": 1}, {"file_id": "large", "file_size": 4}])
        self.assertEqual("large", parse_update(update, "99").attachment.file_id)

    def test_ignores_unrelated_unauthorized_and_unsupported_updates(self):
        cases = [self.message(text="hello"), self.message(text="/tggo no", chat=88), {"update_id": 3, "edited_message": self.message(text="/tggo no")["message"]}, {"update_id": 3, "channel_post": self.message(text="/tggo no")["message"]}]
        for update in cases:
            with self.subTest(update=update):
                self.assertIsNone(parse_update(update, "99"))


if __name__ == "__main__":
    unittest.main()
