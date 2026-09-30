from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from validate_run import expected_reasons
from decisions import display_group_labels, percent


def test_percent():
    assert percent(1, 4) == 25.0
    assert percent(0, 0) == 0.0


def test_display_group_labels_blanks_repeated_hierarchy():
    first = {"language": "en", "source": "MultiSim", "corpus": "ASSET"}
    same_source = {"language": "en", "source": "MultiSim", "corpus": "WikiAutoEN"}
    new_source = {"language": "en", "source": "Other", "corpus": "ASSET"}
    new_language = {"language": "es", "source": "Other", "corpus": "ASSET"}

    assert display_group_labels(first, None) == ("en", "MultiSim", "ASSET")
    assert display_group_labels(same_source, first) == ("", "", "WikiAutoEN")
    assert display_group_labels(new_source, same_source) == ("", "Other", "ASSET")
    assert display_group_labels(new_language, new_source) == ("es", "Other", "ASSET")


def test_confident_simple_target_filter_uses_mc_mean_label_and_smp():
    config = {
        "filters": {
            "smp_threshold": 0.1,
            "labse_min": 0.62,
            "labse_max": 0.95,
            "require_target_confidently_simple": True,
        }
    }
    complexity = {
        "original": {
            "predicted_label": "complex",
            "smp_max_mean_uncertainty": 0.01,
        },
        "simple": {
            "predicted_label": "simple",
            "mc_mean_predicted_label": "complex",
            "smp_max_mean_uncertainty": 0.09,
        },
    }
    assert expected_reasons(complexity, 0.8, config) == [
        "target_not_confidently_simple"
    ]

    complexity["simple"]["mc_mean_predicted_label"] = "simple"
    assert expected_reasons(complexity, 0.8, config) == []

