#!/usr/bin/env python3
"""Run one or all Phase 1 source converters and the corpus audit."""

from __future__ import annotations

import argparse
import json

from audit_corpora import audit
from convert_align_and_shine import convert as convert_align_and_shine
from convert_multisim import convert as convert_multisim
from convert_simplifyur import convert as convert_simplifyur


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("multisim", "simplifyur", "align-and-shine", "all", "audit-all"),
    )
    args = parser.parse_args()
    if args.command in {"multisim", "all"}:
        print(json.dumps(convert_multisim(), ensure_ascii=False))
    if args.command in {"simplifyur", "all"}:
        print(json.dumps(convert_simplifyur(), ensure_ascii=False))
    if args.command in {"align-and-shine", "all"}:
        print(json.dumps(convert_align_and_shine(), ensure_ascii=False))
    if args.command in {"audit-all", "all"}:
        print(json.dumps(audit(), ensure_ascii=False))


if __name__ == "__main__":
    main()
