"""Losslessly restore canonical order from validated Phase 5 shards."""

from __future__ import annotations

import argparse
import json
import os
from contextlib import ExitStack
from pathlib import Path

from common import atomic_json, selected_records, sha256, shard_root
from run_external_metrics import resolve


def consolidate(config_path: Path, metric_alias: str, num_shards: int) -> Path:
    if num_shards < 2:
        raise ValueError("num_shards must be at least 2.")
    resolved = resolve(config_path.resolve(), metric_alias)
    roots = [shard_root(resolved["metric_root"], i, num_shards) for i in range(num_shards)]
    for index, root in enumerate(roots):
        validation = root / "reports" / "validation.json"
        if not validation.is_file() or not json.loads(validation.read_text())["valid"]:
            raise ValueError(f"Shard {index} has not passed validation.")
    output = resolved["metric_root"] / "predictions.jsonl"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite immutable output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + f".tmp-{os.getpid()}")
    count = 0
    with ExitStack() as stack:
        handles = [stack.enter_context((root / "predictions.jsonl").open(encoding="utf-8")) for root in roots]
        target = stack.enter_context(temporary.open("w", encoding="utf-8"))
        for index, source in enumerate(selected_records(resolved["input_path"])):
            line = handles[index % num_shards].readline()
            if not line:
                raise ValueError(f"Shard {index % num_shards} ended early.")
            row = json.loads(line)
            if row.get("canonical_pair_id") != source["canonical_pair_id"]:
                raise ValueError(f"Canonical order mismatch at row {index}.")
            row.pop("shard_index", None)
            target.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
        if any(handle.readline() for handle in handles):
            raise ValueError("At least one shard contains extra rows.")
    os.replace(temporary, output)
    first_config = json.loads((roots[0] / "run_config.json").read_text())
    first_config.update({
        "schema": "feats-phase5-external-metric-sharded-run-v1",
        "status": "complete",
        "shard": None,
        "shard_count": num_shards,
        "processed_pairs": count,
        "output_sha256": sha256(output),
    })
    atomic_json(resolved["metric_root"] / "run_config.json", first_config)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--metric-alias", required=True)
    parser.add_argument("--num-shards", required=True, type=int)
    args = parser.parse_args()
    print(consolidate(args.config, args.metric_alias, args.num_shards))


if __name__ == "__main__":
    main()

