# Phase 6 source layout

Run scripts as modules from the repository root, for example:

```bash
python -m phase6_degraded_corpus.src.selection.select_multi_axis_inputs --help
```

| Package | Responsibility |
|---|---|
| `common/` | JSONL contracts, hashing, and deterministic helpers |
| `selection/` | Meaning-pilot and full multi-axis input selection |
| `planning/` | Cue detection, applicability, and target-axis assignment |
| `generation/` | Qwen inference, retries, reparsing, merging, and consolidation |
| `evaluation/` | Quality analysis and train/validation materialization |
| `reporting/` | Build the single combined pilot report; legacy renderers are retained only for reproducing earlier run artifacts |

The workflow order is selection → planning → generation → evaluation → reporting.

The canonical human-readable pilot output is
[`../docs/PILOT_REPORT.md`](../docs/PILOT_REPORT.md). Do not publish separate
Meaning or per-run pilot reports.
