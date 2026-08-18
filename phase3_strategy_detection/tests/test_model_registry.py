from pathlib import Path
import sys


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from model_registry import create_backend  # noqa: E402


def test_registry_constructs_qwen_without_loading_weights(tmp_path):
    backend = create_backend(
        {
            "backend": "qwen_pairwise",
            "alias": "qwen-test",
            "model_id": "owner/adapter",
            "revision": "a" * 40,
            "base_model_id": "owner/base",
            "base_revision": "b" * 40,
            "quantization": {
                "load_in_4bit": True,
                "quant_type": "nf4",
                "compute_dtype": "bfloat16",
                "double_quant": True,
            },
        },
        cache_root=tmp_path,
    )

    assert backend.alias == "qwen-test"
    assert backend.model is None
