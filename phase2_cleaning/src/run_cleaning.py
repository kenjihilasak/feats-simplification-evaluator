"""Entry point for the reproducible Phase 2 pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import complexity
import decisions
import labse
from common import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=("complexity", "labse", "decisions", "all"), default="all")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.stage in ("complexity", "all"):
        complexity.run(config)
    if args.stage in ("labse", "all"):
        labse.run(config)
    if args.stage in ("decisions", "all"):
        decisions.run(config)


if __name__ == "__main__":
    main()
