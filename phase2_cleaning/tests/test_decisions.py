from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from decisions import percent


def test_percent():
    assert percent(1, 4) == 25.0
    assert percent(0, 0) == 0.0

