"""Score frozen reference-free Phase 7 pairs with pinned Phase 5 backends."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contracts import read_jsonl, write_jsonl

ROOT = Path(__file__).resolve().parents[2]
PHASE5_SRC = ROOT / "phase5_external_metrics" / "src"
sys.path.insert(0, str(PHASE5_SRC))

from model_registry import create_backend  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, default=ROOT / "cache" / "huggingface")
    args = parser.parse_args()
    config = json.loads(args.model_config.read_text(encoding="utf-8"))
    rows = list(read_jsonl(args.input))
    backend = create_backend(config, args.cache_root)
    output = []
    try:
        backend.prepare()
        # LENS manages its own DataLoader; avoid one Lightning Trainer per small batch.
        outer_batch_size = len(rows) if config["backend"] == "lens_salsa" else backend.batch_size
        for start in range(0, len(rows), outer_batch_size):
            batch = rows[start:start + outer_batch_size]
            predictions = backend.predict_batch([(row["original"], row["simple"]) for row in batch])
            output.extend({**row, config["score_field"]: prediction.score,
                           "metric_diagnostics": prediction.diagnostics}
                          for row, prediction in zip(batch, predictions))
    finally:
        backend.close()
    write_jsonl(args.output, output)


if __name__ == "__main__":
    main()
