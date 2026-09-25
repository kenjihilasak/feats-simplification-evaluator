import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase6_degraded_corpus.src.generation.merge_generation_retries import merge
from phase6_degraded_corpus.src.generation.select_generation_retries import select


class RetryTests(unittest.TestCase):
    def test_selects_status_and_overlays_in_base_order(self):
        manifest = [
            {"canonical_pair_id": "pair:1", "target_axis": "SYN"},
            {"canonical_pair_id": "pair:2", "target_axis": "MOD"},
        ]
        generated = [
            {"canonical_pair_id": "pair:1", "status": "failed_parse"},
            {"canonical_pair_id": "pair:2", "status": "generated_pending_audit"},
        ]
        retry_manifest, report = select(manifest, generated, {"failed_parse"})
        self.assertEqual([row["canonical_pair_id"] for row in retry_manifest], ["pair:1"])
        self.assertEqual(report["by_axis"], {"SYN": 1})
        output, merge_report = merge(generated, [{"canonical_pair_id": "pair:1", "status": "failed_validation"}])
        self.assertEqual([row["canonical_pair_id"] for row in output], ["pair:1", "pair:2"])
        self.assertEqual(merge_report["transitions"], {"failed_parse->failed_validation": 1})

    def test_rejects_duplicate_retry_ids(self):
        base = [{"canonical_pair_id": "pair:1", "status": "failed_parse"}]
        retry = {"canonical_pair_id": "pair:1", "status": "failed_validation"}
        with self.assertRaisesRegex(ValueError, "duplicate canonical_pair_id"):
            merge(base, [retry, retry])


if __name__ == "__main__":
    unittest.main()
