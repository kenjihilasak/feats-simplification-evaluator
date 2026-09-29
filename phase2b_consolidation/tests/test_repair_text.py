import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "phase2b_consolidation" / "src"
sys.path.insert(0, str(SRC))

from repair_text import process_root, repair_field, repair_record
from validate_text_repair import validate


class RepairTextTests(unittest.TestCase):
    def test_r1_must_change(self):
        cases = {
            "actor.Haugen": "actor. Haugen", "Paris.He": "Paris. He",
            "in 1994.Ricardo": "in 1994. Ricardo", "(yeux).Un": "(yeux). Un",
            "Prendete il burattino!Prendete": "Prendete il burattino! Prendete",
            "tem 35 anos.No sábado": "tem 35 anos. No sábado",
            "Новый Эрмитаж.С XVIII": "Новый Эрмитаж. С XVIII",
            'reporters.A "press': 'reporters. A "press',
            "Australia.It is": "Australia. It is",
            "in the 1960s.This": "in the 1960s. This",
            "San Francisco 49ers.He": "San Francisco 49ers. He",
            "rapper 2Pac.The": "rapper 2Pac. The",
            "835100 km2.This": "835100 km2. This",
            "band DragonForce.The": "band DragonForce. The",
        }
        for raw, expected in cases.items():
            language = "ru" if "Эрмитаж" in raw else ("pt-BR" if "sábado" in raw else "en")
            self.assertEqual(repair_field(raw, language, "simple")[0], expected, raw)

    def test_r1_must_not_change(self):
        cases = [
            "U.S.The", "J.R.R.Tolkien", "St.Louis", "Dr.Smith", "Fokker Dr.I",
            "a.C. Durante", "av.J.C.", "B.A.", "750 куб.см", "IslamAnswers.Net",
            "todosjuntos.eu", "insieme-per.eu", "France.tv", "Musical.ly",
            "Kheops-Pyramid.jpg|", "DD 01.JPG|", "http://x.org/A.Html",
            "4.essiccamento", "3.5 GHz", "site.Com", "S.p.A. is",
        ]
        for raw in cases:
            self.assertEqual(repair_field(raw, "en", "simple")[0], raw, raw)

    def test_r2_cleanup_order_and_idempotence(self):
        raw = "actor.-LRB- x -RRB-.Haugen"
        repaired, changes = repair_field(raw, "en", "simple")
        self.assertEqual(repaired, "actor.(x). Haugen")
        self.assertEqual([x["rule"] for x in changes], ["R2_ptb_bracket", "R2_ptb_bracket", "R1_glued_sentence"])
        self.assertEqual(repair_field(repaired, "en", "simple"), (repaired, []))
        self.assertEqual(repair_field('Shakespeare."Hamlet"', "en", "simple")[0], 'Shakespeare. "Hamlet"')
        self.assertEqual(repair_field('He said "yes."Then left.', "en", "simple")[0], 'He said "yes." Then left.')
        r2_cases = {
            "Karl-LRB- Charly -RRB-": "Karl (Charly)",
            "nom -LRB- , né -RRB-": "nom (né)",
            "nom -LRB- ; né -RRB-": "nom (né)",
            "texte -LRB- -RRB- suite": "texte suite",
        }
        for raw_r2, expected_r2 in r2_cases.items():
            self.assertEqual(repair_field(raw_r2, "fr", "simple")[0], expected_r2)
        self.assertEqual(repair_field("Karl( Charly )", "fr", "simple")[0], "Karl( Charly )")

    def test_language_gate(self):
        for language in ("ja", "ur", "ar"):
            self.assertEqual(repair_field("actor.Haugen -LRB- x -RRB-", language, "simple")[1], [])

    def test_record_round_trip_fields(self):
        raw = {"language": "en", "original": "actor.Haugen", "simple": "x.Y", "canonical_pair_id": "p2", "canonical_original_id": "o1"}
        value = repair_record(raw)
        self.assertEqual(value["original_raw"], raw["original"])
        self.assertEqual(value["simple_raw"], raw["simple"])
        self.assertTrue(value["text_repaired"])
        self.assertEqual(value["canonical_pair_id"], "p2")

    def test_duplicate_marking_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); inp = root / "input/en"; inp.mkdir(parents=True)
            rows = [
                {"language": "en", "original": "Same", "simple": "actor.Haugen", "canonical_pair_id": "p2", "canonical_original_id": "o1", "corpora": [{"corpus": "WikiAutoEN"}]},
                {"language": "en", "original": "Same", "simple": "actor. Haugen", "canonical_pair_id": "p1", "canonical_original_id": "o1", "corpora": [{"corpus": "WikiAutoEN"}]},
            ]
            (inp / "feats_consolidated.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
            process_root(root / "input", root / "output", root / "reports", seed=1)
            values = [json.loads(x) for x in (root / "output/en/feats_consolidated.jsonl").read_text().splitlines()]
            self.assertEqual(values[0]["repaired_duplicate_of"], "p1")
            self.assertIsNone(values[1]["repaired_duplicate_of"])
            result = validate(root / "input", root / "output")
            self.assertTrue(result["valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
