from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

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

