import csv
import json
import sys
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from analyze_metrics import analyze
from analyze_strata import analyze as analyze_strata


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def fixtures(tmp_path):
    inputs = [{
        "canonical_pair_id": f"pair:en:{i}",
        "canonical_original_id": f"original:en:{i // 2}",
        "language": "en", "original": f"Original {i}", "simple": f"Simple {i}",
        "corpora": [{"source": "Test", "corpus": "Corpus"}],
        "provenance": [{"id": f"occ:{i}"}],
    } for i in range(4)]
    input_path = tmp_path / "input.jsonl"
    lens_path, referee_path = tmp_path / "lens.jsonl", tmp_path / "referee.jsonl"
    write_jsonl(input_path, inputs)
    write_jsonl(lens_path, [{"canonical_pair_id": f"pair:en:{i}", "score": float(i)} for i in range(4)])
    write_jsonl(referee_path, [{"canonical_pair_id": f"pair:en:{i}", "score": float(3 - i)} for i in range(4)])
    return inputs, input_path, lens_path, referee_path


def test_rank_and_human_analysis_excludes_uncertain(tmp_path):
    _, input_path, lens_path, referee_path = fixtures(tmp_path)
    human_path = tmp_path / "human.csv"
    with human_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["canonical_pair_id", "judgment"])
        writer.writeheader()
        writer.writerows([
            {"canonical_pair_id": "pair:en:0", "judgment": "incorrect"},
            {"canonical_pair_id": "pair:en:1", "judgment": "uncertain"},
            {"canonical_pair_id": "pair:en:2", "judgment": "correct"},
            {"canonical_pair_id": "pair:en:3", "judgment": "correct"},
        ])
    report = analyze(input_path, lens_path, referee_path, tmp_path / "reports", human_path, 20)
    assert report["rank_agreement"]["spearman"] == -1.0
    assert report["human_evaluation"]["determinate"] == 3
    assert report["human_evaluation"]["uncertain_excluded"] == 1
    assert (tmp_path / "reports/largest_rank_disagreements.csv").is_file()


def test_strata_analysis_joins_audit_sidecars(tmp_path):
    _, input_path, lens_path, referee_path = fixtures(tmp_path)
    decisions = tmp_path / "decisions/en/source.jsonl"
    write_jsonl(decisions, [{
        "id": f"occ:{i}", "labse_similarity": .7 + i * .05,
        "complexity": {
            "original": {"prob_simple": .2},
            "simple": {"prob_simple": .6},
        },
    } for i in range(4)])
    strategies = tmp_path / "strategies.jsonl"
    write_jsonl(strategies, [{"canonical_pair_id": f"pair:en:{i}", "predicted_codes": ["SYN"]} for i in range(4)])
    report = analyze_strata(
        input_path, lens_path, referee_path, tmp_path / "decisions",
        strategies, tmp_path / "strata",
    )
    assert report["pairs"] == 4
    assert report["multiple_simplifications"]["canonical_original_groups"] == 2
    assert (tmp_path / "strata/metric_distributions_by_stratum.csv").is_file()
