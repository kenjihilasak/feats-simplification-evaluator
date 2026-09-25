import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "phase6_degraded_corpus" / "src"))

from generate_degradations import automatic_checks, parse_generation
from multi_axis import AXES, allocate, applicability
from plan_multi_axis_degradations import plan
from select_multi_axis_inputs import build_inventory
from validate_and_materialize import validate_and_build


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def candidate(index: int, strategy: str) -> dict:
    return {
        "schema": "feats-phase6-clean-candidate-v2",
        "canonical_pair_id": f"pair:{index}",
        "canonical_original_id": f"original:{index // 2}",
        "language": "en",
        "original": "Could Alice explain the difficult process in London in 1999?",
        "clean_simplification": "Alice may explain the process in London in 1999.",
        "source": "MultiSim", "corpus": "WikiAutoEN", "source_strategy": strategy,
        "clean_source_tier": "weak", "clean_review_status": "weak_supervision_candidate",
    }


class MultiAxisTests(unittest.TestCase):
    def test_applicability_separates_source_and_target(self):
        found = applicability(candidate(1, "SYN"))
        self.assertTrue(found["SYN"])
        self.assertFalse(found["OMIT"])
        self.assertTrue(found["MEANING"])
        self.assertTrue(found["FLUENCY"])
        self.assertTrue(found["ILLOC"])

    def test_allocator_is_deterministic_unique_and_protects_mod(self):
        strategies = ["MOD"] * 3 + ["OMIT"] * 8 + ["SYN"] * 8 + ["EXPL"] * 8 + ["COMP"] * 8
        rows = [candidate(index, strategy) for index, strategy in enumerate(strategies)]
        first, report1 = allocate(rows, 11)
        second, report2 = allocate(rows, 11)
        self.assertEqual(first, second)
        self.assertEqual(report1, report2)
        self.assertEqual(len(first), len({row["canonical_pair_id"] for row in first}))
        self.assertEqual({row["target_axis"] for row in first if row["source_strategy"] == "MOD"}, {"MOD"})
        self.assertTrue(all(row["target_axis"] in row["applicable_axes"] for row in first))
        self.assertEqual(set(report1["assigned_by_axis"]), set(AXES))

    def test_planner_selects_fifty_for_each_non_frozen_axis(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            strategies = ["OMIT", "SYN", "MOD", "EXPL", "COMP", "SYNT"]
            rows = [candidate(index, strategies[index % len(strategies)]) for index in range(1200)]
            path = tmp / "inventory.jsonl"
            write_jsonl(path, rows)
            assignments, pilots, report = plan({
                "experiment_id": "test", "seed": 5, "input_file": str(path),
                "pilot_size_per_axis": 50, "frozen_pilot_axes": ["MEANING"],
            })
            self.assertEqual(len(assignments), len(rows))
            self.assertEqual(len(pilots), 300)
            self.assertEqual(set(report["pilot_by_axis"]), set(AXES) - {"MEANING"})

    def test_inventory_intersects_strict_candidates_and_excludes_asset(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            phase2, strict = [], []
            for index, corpus in enumerate(["WikiAutoEN", "ASSET"]):
                phase2.append({
                    "canonical_pair_id": f"pair:{index}", "canonical_original_id": f"original:{index}",
                    "language": "en", "original": "one two three four five six seven eight nine",
                    "simple": "one two three four five", "corpora": [{"source": "MultiSim", "corpus": corpus}],
                })
                strict.append({
                    "canonical_pair_id": f"pair:{index}", "candidate_strategy_code": "OMIT",
                    "quality_tier": "strict", "confirmation_count": 1,
                })
            write_jsonl(tmp / "phase2.jsonl", phase2)
            write_jsonl(tmp / "strict.jsonl", strict)
            rows, report = build_inventory({
                "experiment_id": "test", "language": "en", "phase2b_file": str(tmp / "phase2.jsonl"),
                "single_strategy_file": str(tmp / "strict.jsonl"), "phase2b_variant_id": "p2",
                "phase3a_candidate_set_id": "p3", "allowed_corpora": ["WikiAutoEN"],
                "excluded_corpora": ["ASSET"], "reserved_original_ids_files": [],
                "original_token_range": [8, 45],
            })
            self.assertEqual([row["canonical_pair_id"] for row in rows], ["pair:0"])
            self.assertEqual(report["exclusions"]["corpus"], 1)

    def test_generation_parser_and_checks(self):
        row = {**candidate(1, "SYN"), "assigned_operation": "restore_complex_lexical_item"}
        parsed = parse_generation(json.dumps({
            "degraded_simplification": "Alice may elucidate the process.", "changed_span": "explain",
            "replacement_span": "elucidate", "operation_type": "restore_complex_lexical_item",
            "brief_verification": "one change",
        }))
        checks = automatic_checks(row, parsed)
        self.assertTrue(checks["different_from_clean"])
        self.assertTrue(checks["operation_matches_assignment"])
        spaced = parse_generation(json.dumps({
            **parsed,
            " degraded_simplification": parsed["degraded_simplification"],
        }).replace('"degraded_simplification":', '"ignored":', 1))
        self.assertEqual(spaced["degraded_simplification"], parsed["degraded_simplification"])
        with self.assertRaises(ValueError):
            parse_generation("{}")

    def test_materialization_groups_original_and_balances_variants(self):
        manifest, generated, audits = [], [], []
        for index in range(4):
            row = {**candidate(index, "SYN"), "target_axis": "SYN"}
            manifest.append(row)
            generated.append({
                "canonical_pair_id": row["canonical_pair_id"], "target_axis": "SYN", "source_strategy": "SYN",
                "status": "generated_pending_audit", "model_revision": "abc", "prompt_id": "syn_degradation_v1",
                "generation": {"degraded_simplification": f"degraded {index}"},
            })
            audits.append({
                "canonical_pair_id": row["canonical_pair_id"], "decision": "accepted",
                "clean_acceptable": True, "single_target_degradation": True,
                "meaning_preserved_for_non_meaning": True,
            })
        instances, report = validate_and_build(manifest, generated, audits, 7)
        self.assertEqual(len(instances), 8)
        self.assertEqual(report["accepted_pairs"], 4)
        by_original = {}
        for row in instances:
            by_original.setdefault(row["canonical_original_id"], set()).add(row["split"])
        self.assertTrue(all(len(splits) == 1 for splits in by_original.values()))
        with self.assertRaises(ValueError):
            validate_and_build(manifest + [manifest[0]], generated, audits, 7)


if __name__ == "__main__":
    unittest.main()
