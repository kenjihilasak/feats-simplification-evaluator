from pathlib import Path
import sys

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from common import input_files


def test_input_files_honors_explicit_selection(tmp_path):
    selected = tmp_path / "ar" / "selected.jsonl"
    ignored = tmp_path / "en" / "ignored.jsonl"
    selected.parent.mkdir()
    ignored.parent.mkdir()
    selected.write_text("{}\n", encoding="utf-8")
    ignored.write_text("{}\n", encoding="utf-8")

    files = input_files({"input_root": str(tmp_path), "include_files": ["ar/selected.jsonl"]})

    assert [item.path for item in files] == [selected]


def test_input_files_rejects_missing_explicit_input(tmp_path):
    with pytest.raises(FileNotFoundError, match="matched no JSONL"):
        input_files({"input_root": str(tmp_path), "include_files": ["es/missing.jsonl"]})
