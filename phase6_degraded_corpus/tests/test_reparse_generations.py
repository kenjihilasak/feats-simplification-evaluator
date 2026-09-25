import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase6_degraded_corpus" / "src"))

from reparse_generations import reparse


class ReparseTests(unittest.TestCase):
    def test_repairs_whitespace_prefixed_key_without_inference(self):
        plan = [{
            "canonical_pair_id": "pair:1", "clean_simplification": "Alice explains it.",
            "assigned_operation": "restore_complex_lexical_item",
        }]
        response = {
            " degraded_simplification": "Alice elucidates it.", "changed_span": "explains",
            "replacement_span": "elucidates", "operation_type": "restore_complex_lexical_item",
            "brief_verification": "one replacement",
        }
        generated = [{
            "canonical_pair_id": "pair:1", "status": "failed_parse",
            "raw_response": json.dumps(response), "generation": None,
        }]
        rows, report = reparse(plan, generated)
        self.assertEqual(rows[0]["status"], "generated_pending_audit")
        self.assertEqual(report["transitions"], {"failed_parse->generated_pending_audit": 1})


if __name__ == "__main__":
    unittest.main()
