"""Run the public LENS-SALSA and REFEREE examples before a pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import load_json, project_path
from model_registry import create_backend


LENS_PAIR = (
    "They are culturally akin to the coastal peoples of Papua New Guinea.",
    "They are culturally similar to the people of Papua New Guinea.",
)
REFEREE_PAIRS = (
    (
        "In late 2004, Suleman made headlines by cutting Howard Stern's radio show from four Citadel stations, citing Stern's frequent discussions regarding his upcoming move to Sirius Satellite Radio.",
        "In late 2004, suleman made headlines by cutting howard stern 's radio show from four citadel stations.",
    ),
    (
        "In late 2004, Suleman made headlines by cutting Howard Stern's radio show from four Citadel stations, citing Stern's frequent discussions regarding his upcoming move to Sirius Satellite Radio.",
        "In late 2004, suleman made headlines by cutting howard stern 's radio show from four citadel stations, referring to Stern's frequent discussions regarding his upcoming move to Sirius Satellite Radio.",
    ),
)


def verify(model_config: Path, cache_root: Path) -> dict:
    config = load_json(model_config)
    backend = create_backend(config, cache_root)
    try:
        backend.prepare()
        pairs = [LENS_PAIR] if config["alias"] == "lens_salsa" else list(REFEREE_PAIRS)
        scores = [item.score for item in backend.predict_batch(pairs)]
        result = {"metric_alias": config["alias"], "scores": scores, "model": dict(backend.provenance())}
        if config["alias"] == "lens_salsa":
            result["published_example_score"] = 72.40909337997437
            result["absolute_difference"] = abs(scores[0] - result["published_example_score"])
        return result
    finally:
        backend.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-config", required=True, type=Path)
    parser.add_argument("--cache-root", type=Path, default=Path("cache/huggingface"))
    args = parser.parse_args()
    print(json.dumps(verify(project_path(args.model_config), project_path(args.cache_root)), indent=2))


if __name__ == "__main__":
    main()
