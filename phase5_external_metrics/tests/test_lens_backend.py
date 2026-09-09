import sys
from pathlib import Path
from types import SimpleNamespace


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from lens_backend import LensSalsaBackend


class FakeTokenizer:
    def num_special_tokens_to_add(self, pair=False):
        return 4 if pair else 2

    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(f"t{value}" for value in ids)


def test_lens_balanced_truncation_respects_combined_budget(tmp_path):
    backend = LensSalsaBackend({
        "alias": "lens_salsa", "repo_id": "test", "revision": "test",
    }, tmp_path)
    encoder = SimpleNamespace(tokenizer=FakeTokenizer(), size_separator=2, max_positions=20)
    backend.model = SimpleNamespace(model=SimpleNamespace(encoder=encoder))
    source, target, diagnostics = backend._truncate_pair(
        " ".join(["source"] * 20), " ".join(["target"] * 20)
    )
    assert diagnostics["combined_subwords_before_truncation"] == 40
    assert diagnostics["combined_subword_budget"] == 16
    assert diagnostics["truncated"] is True
    assert len(source.split()) + len(target.split()) == 16


def test_lens_short_pair_is_not_rewritten(tmp_path):
    backend = LensSalsaBackend({
        "alias": "lens_salsa", "repo_id": "test", "revision": "test",
    }, tmp_path)
    encoder = SimpleNamespace(tokenizer=FakeTokenizer(), size_separator=2, max_positions=20)
    backend.model = SimpleNamespace(model=SimpleNamespace(encoder=encoder))
    source, target, diagnostics = backend._truncate_pair("one two", "three four")
    assert (source, target) == ("one two", "three four")
    assert diagnostics["truncated"] is False
