#!/usr/bin/env python3
"""Freeze original texts from the evaluation corpora used by Phase 6.

The upstream repositories/archive must already exist under ``--source-root``.
This script does not alter upstream files. It records their hashes and creates a
deduplicated, normalized exclusion list for pool selection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path


SPACE_RE = re.compile(r"\s+")
WORD_CHARACTER_RE = re.compile(r"[^\W_]", re.UNICODE)
PTB_BRACKETS = {
    "-lrb-": "(", "-rrb-": ")", "-lsb-": "[",
    "-rsb-": "]", "-lcb-": "{", "-rcb-": "}",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def weak_key(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip().casefold()


def strong_key(text: str) -> str:
    """Return the evaluation-reservation key defined in plan section 0.3."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    for token, bracket in PTB_BRACKETS.items():
        normalized = normalized.replace(token, bracket)
    return "".join(WORD_CHARACTER_RE.findall(normalized))


def read_csv_column(path: Path, column: str) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if column not in (reader.fieldnames or []):
            raise ValueError(f"Missing column {column!r} in {path}")
        return [row[column].strip() for row in reader if row[column].strip()]


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def git_revision(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.source_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    specifications = [
        {
            "name": "simplicity_da",
            "repo": "simplicity_da",
            "url": "https://github.com/feralvam/metaeval-simplification.git",
            "relative_path": "simplicity_da/data/simplicity_DA.csv",
            "reader": lambda path: read_csv_column(path, "orig_sent"),
        },
        {
            "name": "human_likert",
            "repo": "questeval",
            "url": "https://dl.fbaipublicfiles.com/questeval/simplification_human_evaluations.tar.gz",
            "relative_path": "questeval_human_evaluations/simplification_human_evaluations/questeval_simplification_likert_ratings.csv",
            "reader": lambda path: read_csv_column(path, "source"),
        },
        {
            "name": "assetann",
            "repo": "assetann",
            "url": "https://github.com/remicardon/assetann.git",
            "relative_path": "assetann/sets/asset-full/asset.orig.txt",
            "reader": read_lines,
        },
        {
            "name": "simpeval_2022",
            "repo": "lens_heineman",
            "url": "https://github.com/davidheineman/lens.git",
            "relative_path": "lens_heineman/data/simpeval_2022.csv",
            "reader": lambda path: read_csv_column(path, "original"),
        },
        {
            "name": "asset_official_test",
            "repo": "asset",
            "url": "https://github.com/facebookresearch/asset.git",
            "relative_path": "asset/dataset/asset.test.orig",
            "reader": read_lines,
        },
    ]

    manifest_sources = []
    weak_forms: dict[str, str] = {}
    representatives: dict[str, str] = {}
    membership: dict[str, set[str]] = {}
    forms_by_key: dict[str, set[str]] = {}
    for spec in specifications:
        path = root / spec["relative_path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        texts = spec["reader"](path)
        weak_normalized = {weak_key(text): text for text in texts if weak_key(text)}
        normalized = {strong_key(text): text for text in texts if strong_key(text)}
        weak_forms.update(weak_normalized)
        for text in texts:
            key = strong_key(text)
            if not key:
                continue
            representatives.setdefault(key, text)
            membership.setdefault(key, set()).add(spec["name"])
            forms_by_key.setdefault(key, set()).add(weak_key(text))
        manifest_sources.append(
            {
                "name": spec["name"],
                "url": spec["url"],
                "repository_revision": git_revision(root / spec["repo"]),
                "relative_path": spec["relative_path"],
                "sha256": sha256(path),
                "row_count": len(texts),
                "unique_weak_forms": len(weak_normalized),
                "unique_normalized_originals": len(normalized),
            }
        )

    ordered_keys = sorted(representatives)
    reserved_path = output_dir / "reserved_original_texts.txt"
    reserved_path.write_text(
        "".join(f"{representatives[key]}\n" for key in ordered_keys), encoding="utf-8"
    )

    membership_path = output_dir / "reserved_original_membership.jsonl"
    with membership_path.open("w", encoding="utf-8") as handle:
        for key in ordered_keys:
            handle.write(
                json.dumps(
                    {
                        "strong_key": key,
                        "original": representatives[key],
                        "sources": sorted(membership[key]),
                        "weak_forms": sorted(forms_by_key[key]),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

    archive = root / "questeval_simplification_human_evaluations.tar.gz"
    manifest = {
        "schema": "feats-phase6-evaluation-originals-v2",
        "normalization": {
            "weak_form": "collapse whitespace, strip, Unicode casefold",
            "strong_key": (
                "NFKC, casefold, PTB brackets to brackets, then keep only "
                "Unicode word characters except underscore"
            ),
        },
        "counts": {
            "weak_forms": len(weak_forms),
            "distinct_sentences_strong_key": len(ordered_keys),
        },
        "sources": manifest_sources,
        "download_archives": [
            {
                "url": "https://dl.fbaipublicfiles.com/questeval/simplification_human_evaluations.tar.gz",
                "relative_path": archive.name,
                "sha256": sha256(archive),
                "size_bytes": archive.stat().st_size,
            }
        ],
        "outputs": {
            "reserved_original_texts": {
                "relative_path": reserved_path.name,
                "count": len(ordered_keys),
                "sha256": sha256(reserved_path),
            },
            "membership": {
                "relative_path": membership_path.name,
                "count": len(ordered_keys),
                "sha256": sha256(membership_path),
            },
        },
    }
    manifest_path = output_dir / "evaluation_sources_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"counts": manifest["counts"], "outputs": manifest["outputs"]}, indent=2))


if __name__ == "__main__":
    main()
