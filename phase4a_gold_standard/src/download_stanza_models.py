#!/usr/bin/env python3
"""Download the exact Stanza UD packages pinned by the Phase 4a config."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .build_stanza_syntax_sidecars import model_metadata
    from .data_contracts import SYNTAX_CONFIG_SCHEMA, load_json, project_path
except ImportError:
    from build_stanza_syntax_sidecars import model_metadata
    from data_contracts import SYNTAX_CONFIG_SCHEMA, load_json, project_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = (
    PROJECT_ROOT / "phase4a_gold_standard" / "configs" / "stanza_ud_syntax_v1.json"
)


def download(config_path: Path, languages: list[str] | None = None) -> None:
    config = load_json(config_path.resolve())
    if config.get("schema") != SYNTAX_CONFIG_SCHEMA:
        raise ValueError("Unexpected syntax config schema")
    configured = config.get("languages")
    if not isinstance(configured, dict) or not configured:
        raise ValueError("No languages are configured")
    selected = sorted(languages or configured)
    unknown = set(selected) - set(configured)
    if unknown:
        raise ValueError(f"Unknown configured languages: {sorted(unknown)}")

    import stanza

    expected_version = str(config["stanza_version"])
    if str(stanza.__version__) != expected_version:
        raise RuntimeError(
            f"Stanza {stanza.__version__} does not match pin {expected_version}"
        )
    model_dir = project_path(config["model_dir"])
    model_dir.mkdir(parents=True, exist_ok=True)
    for language in selected:
        metadata = model_metadata(config, language)
        stanza.download(
            lang=metadata["language"],
            model_dir=str(model_dir),
            package=metadata["packages"],
            processors="tokenize,pos,lemma,depparse",
            resources_version=metadata["resources_version"],
            download_json=True,
            verbose=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--language", action="append", dest="languages")
    args = parser.parse_args()
    download(args.config, args.languages)


if __name__ == "__main__":
    main()
