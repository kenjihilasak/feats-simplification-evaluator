"""Maintenance and server CLI for Phase 4a."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from .constants import MAX_IMPORT_BATCH
from .reports import build_report, render_csv, render_jsonl
from .security import canonical_json
from .service import AnnotationService, ServiceSettings


def _records(path: Path) -> Iterable[dict[str, Any]]:
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number} is not a JSON object")
                yield value
        return
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and isinstance(value.get("tasks"), list):
        value = value["tasks"]
    elif isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("JSON input must be a task, a task list, or an object with tasks")
    yield from value


def _write(value: str, output: Path | None) -> None:
    if output is None:
        sys.stdout.write(value)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value, encoding="utf-8")


def _import_in_batches(
    service: AnnotationService, records: Iterable[dict[str, Any]]
) -> dict[str, int]:
    totals = {"inserted": 0, "unchanged": 0}
    batch: list[dict[str, Any]] = []
    for record in records:
        batch.append(record)
        if len(batch) == MAX_IMPORT_BATCH:
            result = service.import_tasks(batch)
            for key in totals:
                totals[key] += int(result.get(key, 0))
            batch = []
    if batch:
        result = service.import_tasks(batch)
        for key in totals:
            totals[key] += int(result.get(key, 0))
    return totals


def _settings(args: argparse.Namespace) -> ServiceSettings:
    settings = ServiceSettings.from_env()
    if args.database is not None:
        settings = replace(settings, database_path=args.database)
    return settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phase4a-backend")
    parser.add_argument("--database", type=Path, help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="initialise or migrate the database")

    user = subparsers.add_parser("create-user", help="create or update a nominal account")
    user.add_argument("--username", required=True)
    user.add_argument("--display-name", required=True)
    user.add_argument("--role", choices=("reviewer", "admin"), default="reviewer")
    user.add_argument("--language", action="append", default=[])
    user.add_argument("--password", help="omit to be prompted without terminal echo")

    import_parser = subparsers.add_parser("import-tasks", help="import JSON/JSONL tasks")
    import_parser.add_argument("input", type=Path)

    export = subparsers.add_parser("export", help="write a deterministic campaign export")
    export.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    export.add_argument("--output", type=Path)
    export.add_argument("--without-model-votes", action="store_true")

    report = subparsers.add_parser("report", help="write the deterministic quality report")
    report.add_argument("--output", type=Path)

    subparsers.add_parser("progress", help="print administrative progress JSON")

    serve = subparsers.add_parser("serve", help="run the private FastAPI server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = _settings(args)
    try:
        service = AnnotationService(settings)
        if args.command == "init":
            print(f"initialised {service.database.path}")
        elif args.command == "create-user":
            password = args.password or getpass.getpass("Password: ")
            languages = args.language if args.role == "reviewer" else None
            user = service.create_user(
                username=args.username,
                display_name=args.display_name,
                password=password,
                role=args.role,
                allowed_languages=languages,
            )
            print(canonical_json(service.user_payload(user)))
        elif args.command == "import-tasks":
            result = _import_in_batches(service, _records(args.input))
            print(canonical_json(result))
        elif args.command == "export":
            rows = list(
                service.database.iter_export_rows(
                    include_model_votes=not args.without_model_votes
                )
            )
            value = render_jsonl(rows) if args.format == "jsonl" else render_csv(rows)
            _write(value, args.output)
        elif args.command == "report":
            rows = list(service.database.iter_export_rows(include_model_votes=True))
            value = canonical_json(
                build_report(rows, progress=service.database.progress())
            ) + "\n"
            _write(value, args.output)
        elif args.command == "progress":
            print(canonical_json(service.database.progress()))
        elif args.command == "serve":
            try:
                import uvicorn
            except ImportError as error:
                raise RuntimeError(
                    "uvicorn is required; install requirements-runtime.txt"
                ) from error
            from .app import create_app

            uvicorn.run(
                create_app(settings),
                host=args.host,
                port=args.port,
                reload=args.reload,
            )
        return 0
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
