import tempfile
import unittest
from pathlib import Path

from phase4a_gold_standard.backend.s1_database import S1Database


class ReopenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = S1Database(Path(self.tmp.name) / "s1.sqlite3")
        self.db.initialise()
        item = {"case_id": "A", "axis": "SYN", "format": "pair", "original": "x y", "versions": {"X": "a", "Y": "b"}}
        self.db.import_items([item, {**item, "case_id": "B"}], "rev")
        self.draft = {"choice": "X", "note": "my reasons", "ideal_simplification": "mine",
                      "selected_original_words": [{"index": 1, "start": 2, "end": 3, "text": "y"}]}

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_skipped_item_gets_its_last_draft_back(self):
        v = self.db.save("A", "rev", self.draft, 0, False)["version"]
        v = self.db.save("A", "rev", self.draft | {"note": "newer"}, v, False)["version"]
        self.db.save("A", "rev", {"skipped": True, "note": "", "ideal_simplification": ""}, v, True)
        result = self.db.reopen("A")
        self.assertEqual(result["restored_answer"], self.draft | {"note": "newer"})
        task = self.db.get("A", "rev")
        self.assertEqual(task["annotation"]["state"], "draft")
        self.assertEqual(task["annotation"]["answer"]["note"], "newer")
        self.assertEqual(task["annotation"]["version"], 4)
        self.assertEqual(self.db.next("rev")["case_id"], "A")

    def test_a_submitted_answer_is_kept_as_the_draft(self):
        self.db.save("A", "rev", self.draft, 0, True)
        self.assertEqual(self.db.reopen("A")["restored_answer"], self.draft)

    def test_only_submitted_items_can_be_reopened(self):
        self.db.save("B", "rev", self.draft, 0, False)
        with self.assertRaises(ValueError):
            self.db.reopen("B")
        with self.assertRaises(ValueError):
            self.db.reopen("A")


if __name__ == "__main__":
    unittest.main()
