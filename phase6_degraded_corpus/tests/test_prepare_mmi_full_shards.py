import tempfile
import unittest
from pathlib import Path

from phase6_degraded_corpus.src.common.contracts import read_jsonl, write_jsonl
from phase6_degraded_corpus.src.generation.prepare_mmi_full_shards import prepare, validate


class PrepareMmiFullShardsTest(unittest.TestCase):
    def test_model_homogeneous_shards_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root / "plan.jsonl"
            rows = [
                {"canonical_pair_id": "p1", "target_axis": "MEANING", "plan_status": "ready"},
                {"canonical_pair_id": "p2", "target_axis": "ILLOC", "plan_status": "ready"},
                {"canonical_pair_id": "p3", "target_axis": "MOD", "plan_status": "ready"},
                {"canonical_pair_id": "p4", "target_axis": "MOD", "plan_status": "dropped"},
            ]
            write_jsonl(plan, rows)
            report = prepare(plan, root / "shards", 1)
            self.assertEqual(report["ready_rows"], 3)
            manifest = __import__("json").loads((root / "shards/shard_manifest.json").read_text())
            self.assertEqual([item["config_id"] for item in manifest], ["C1", "C1", "C2"])
            first_plan = Path(manifest[0]["plan"])
            first_output = Path(manifest[0]["output"])
            write_jsonl(first_output, read_jsonl(first_plan))
            self.assertTrue(validate(first_plan, first_output))


if __name__ == "__main__":
    unittest.main()
