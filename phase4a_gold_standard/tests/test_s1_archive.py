import sqlite3
import tempfile
import unittest
from pathlib import Path

from phase4a_gold_standard.backend.s1_database import S1Database


def item(case_id):
    return {"case_id": case_id, "axis": "OMIT", "format": "pair", "original": "o", "versions": {"X": "a", "Y": "b"}}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = S1Database(Path(self.dir.name) / "s1.sqlite3")
        self.db.initialise()
        self.db.import_items([item("IT-S001"), item("IT-S002")], "reviewer-it")
        with self.db.connect() as c:
            c.execute("INSERT INTO annotations(case_id,reviewer_username,state,answer_json,version,created_at,updated_at) "
                      "VALUES('IT-S001','reviewer-it','submitted','{\"choice\":\"X\"}',1,'t','t')")
        self.db.import_meta([{"case_id": "IT-S001", "dataset": "d", "human_versions": ["X"]}])

    def tearDown(self):
        self.dir.cleanup()

    def test_archive_keeps_answers_and_frees_the_case_ids(self):
        result = self.db.archive("reviewer-it", "v2")
        self.assertEqual(result, {"archived_items": 2, "submitted_answers": 1, "archived_as": "archive-v2-reviewer-it"})
        with sqlite3.connect(self.db.path) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM items WHERE reviewer_username='reviewer-it'").fetchone()[0], 0)
            row = c.execute("SELECT case_id, reviewer_username, answer_json FROM annotations").fetchone()
            self.assertEqual(row, ("v2:IT-S001", "archive-v2-reviewer-it", '{"choice":"X"}'))
            self.assertEqual(c.execute("SELECT case_id FROM item_meta").fetchone()[0], "v2:IT-S001")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
        # the same case id can be loaded again for the new round
        self.assertEqual(self.db.import_items([item("IT-S001")], "reviewer-it"), {"inserted": 1, "unchanged": 0})

    def test_the_same_label_cannot_be_used_twice(self):
        self.db.archive("reviewer-it", "v2")
        self.db.import_items([item("IT-S001")], "reviewer-it")
        with self.assertRaises(ValueError):
            self.db.archive("reviewer-it", "v2")


if __name__ == "__main__":
    unittest.main()


class MixTests(unittest.TestCase):
    def test_new_items_are_spread_among_pending_ones(self):
        with tempfile.TemporaryDirectory() as d:
            db = S1Database(Path(d) / "s1.sqlite3")
            db.initialise()
            db.import_items([{**item(f"A{i:02d}"), "_queue_rank": i} for i in range(10)], "r")
            with db.connect() as c:
                c.execute("INSERT INTO annotations(case_id,reviewer_username,state,answer_json,version,created_at,updated_at) "
                          "VALUES('A03','r','submitted','{}',1,'t','t')")
            db.import_items([{**item(f"N{i}"), "_queue_rank": 10 + i} for i in range(3)], "r")
            result = db.mix("r", ["N0", "N1", "N2"], keep_first=2, seed=1)
            self.assertEqual(result, {"reviewer": "r", "mixed": 3, "kept_in_front": 3, "total": 13})
            with db.connect() as c:
                order = [r[0] for r in c.execute("SELECT case_id FROM items WHERE reviewer_username='r' ORDER BY queue_rank")]
            self.assertEqual(order[:3], ["A03", "A00", "A01"])            # answered first, then the kept ones
            old = [x for x in order if x.startswith("A")]
            self.assertEqual(old[3:], ["A02", "A04", "A05", "A06", "A07", "A08", "A09"])  # relative order kept
            self.assertNotIn(order[-1][0], "N")                           # not all appended at the end
            self.assertEqual(sorted(x for x in order if x.startswith("N")), ["N0", "N1", "N2"])
