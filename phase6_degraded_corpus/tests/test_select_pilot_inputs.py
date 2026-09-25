import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase6_degraded_corpus.src.selection.select_pilot_inputs import build


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")


class SelectionTests(unittest.TestCase):
    def test_selection_is_deterministic_and_original_disjoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            phase2 = []
            lengths = [10, 11, 12, 13, 17, 18, 20, 28, 30]
            for i, length in enumerate(lengths):
                phase2.append({
                    "canonical_pair_id": f"pair:{i}",
                    "canonical_original_id": f"original:{i}",
                    "language": "en",
                    "original": " ".join(["word"] * length),
                    "simple": f"simplified text {i}",
                    "corpora": [{"source": "MultiSim", "corpus": "WikiAutoEN"}],
                })
            write_jsonl(tmp / "phase2.jsonl", phase2)
            write_jsonl(tmp / "human.jsonl", [{"canonical_pair_id": "pair:0", "human_label": "positive"}])
            write_jsonl(tmp / "strategies.jsonl", [
                {"canonical_pair_id": f"pair:{i}", "predicted_codes": [["SYN", "OMIT", "EXPL"][i % 3]]}
                for i in range(len(phase2))
            ])
            config = {
                "experiment_id": "test", "language": "en", "seed": 7,
                "primary_size": 4, "backup_size": 2,
                "phase2b_file": str(tmp / "phase2.jsonl"),
                "human_judgments_file": str(tmp / "human.jsonl"),
                "strategy_predictions_file": str(tmp / "strategies.jsonl"),
                "allowed_corpora": ["WikiAutoEN"], "excluded_corpora": ["ASSET"],
                "reserved_original_ids_file": None,
                "length_bins": {"short": [8, 15], "medium": [16, 25], "long": [26, 45]},
                "primary_length_targets": {"short": 2, "medium": 1, "long": 1},
            }
            p1, b1, report1 = build(config)
            p2, b2, report2 = build(config)
            self.assertEqual(p1, p2)
            self.assertEqual(b1, b2)
            self.assertEqual(report1, report2)
            self.assertEqual(report1["reviewed_anchors"], 1)
            self.assertEqual(report1["primary_by_length"], {"short": 2, "medium": 1, "long": 1})
            self.assertTrue(all(x["predicted_strategy_count"] == 1 for x in p1 + b1))
            ids = [x["canonical_original_id"] for x in p1 + b1]
            self.assertEqual(len(ids), len(set(ids)))

    def test_excludes_evaluation_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            write_jsonl(tmp / "phase2.jsonl", [{
                "canonical_pair_id": "pair:asset", "canonical_original_id": "original:asset",
                "language": "en", "original": "one two three four five six seven eight",
                "simple": "simpler", "corpora": [{"source": "MultiSim", "corpus": "ASSET"}],
            }])
            write_jsonl(tmp / "human.jsonl", [{"canonical_pair_id": "pair:asset", "human_label": "positive"}])
            write_jsonl(tmp / "strategies.jsonl", [{"canonical_pair_id": "pair:asset", "predicted_codes": ["SYN"]}])
            config = {
                "experiment_id": "test", "language": "en", "seed": 1,
                "primary_size": 0, "backup_size": 0,
                "phase2b_file": str(tmp / "phase2.jsonl"),
                "human_judgments_file": str(tmp / "human.jsonl"),
                "strategy_predictions_file": str(tmp / "strategies.jsonl"),
                "allowed_corpora": ["WikiAutoEN"], "excluded_corpora": ["ASSET"],
                "reserved_original_ids_file": None,
                "length_bins": {"short": [8, 15]}, "primary_length_targets": {},
            }
            primary, backup, report = build(config)
            self.assertEqual(primary, [])
            self.assertEqual(backup, [])
            self.assertEqual(report["exclusions"]["corpus"], 1)


if __name__ == "__main__":
    unittest.main()
