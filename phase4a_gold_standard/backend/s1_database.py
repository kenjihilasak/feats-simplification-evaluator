"""Isolated SQLite persistence for the S1 validation study."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class S1Database:
    """S1 store. This class never opens the Phase 4a database."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def initialise(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS items (
                    case_id TEXT PRIMARY KEY,
                    axis TEXT NOT NULL,
                    format TEXT NOT NULL CHECK(format IN ('pair','rank3')),
                    payload_json TEXT NOT NULL,
                    reviewer_username TEXT NOT NULL,
                    queue_rank INTEGER NOT NULL,
                    is_control INTEGER NOT NULL DEFAULT 0,
                    control_kind TEXT,
                    llm_suggestion_json TEXT,
                    UNIQUE(reviewer_username, queue_rank)
                );
                CREATE TABLE IF NOT EXISTS annotations (
                    case_id TEXT PRIMARY KEY REFERENCES items(case_id),
                    reviewer_username TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','submitted')),
                    answer_json TEXT NOT NULL DEFAULT '{}',
                    version INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revisions (
                    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    reviewer_username TEXT NOT NULL,
                    old_answer_json TEXT NOT NULL,
                    new_answer_json TEXT NOT NULL,
                    old_state TEXT,
                    new_state TEXT NOT NULL,
                    old_version INTEGER NOT NULL,
                    new_version INTEGER NOT NULL,
                    changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS batches (
                    reviewer_username TEXT PRIMARY KEY,
                    finished_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_s1_queue
                    ON items(reviewer_username, queue_rank);
                -- Shown to annotators: the dataset always, the human version only after submission.
                CREATE TABLE IF NOT EXISTS item_meta (
                    case_id TEXT PRIMARY KEY REFERENCES items(case_id),
                    dataset TEXT NOT NULL,
                    human_versions_json TEXT NOT NULL
                );
                """
            )

    def import_items(self, items: Iterable[Mapping[str, Any]], reviewer: str) -> dict[str, int]:
        inserted = unchanged = 0
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for item in items:
                payload = dict(item)
                case_id = str(payload["case_id"])
                is_control = int(bool(payload.pop("_is_control", False)))
                control_kind = payload.pop("_control_kind", None)
                existing = db.execute(
                    "SELECT payload_json, reviewer_username, queue_rank FROM items WHERE case_id=?",
                    (case_id,),
                ).fetchone()
                rank = int(payload.pop("_queue_rank")) if "_queue_rank" in payload else inserted + unchanged
                encoded = _json(payload)
                if existing:
                    if (existing["payload_json"], existing["reviewer_username"], existing["queue_rank"]) != (encoded, reviewer, rank):
                        raise ValueError(f"S1 item {case_id} already exists with different content")
                    unchanged += 1
                    continue
                db.execute(
                    "INSERT INTO items(case_id,axis,format,payload_json,reviewer_username,queue_rank,is_control,control_kind) VALUES(?,?,?,?,?,?,?,?)",
                    (case_id, payload["axis"], payload["format"], encoded, reviewer, rank,
                     is_control, control_kind),
                )
                inserted += 1
            db.execute("INSERT OR IGNORE INTO batches(reviewer_username) VALUES(?)", (reviewer,))
        return {"inserted": inserted, "unchanged": unchanged}

    def import_suggestions(self, rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
        loaded = 0
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for row in rows:
                result = db.execute(
                    "UPDATE items SET llm_suggestion_json=? WHERE case_id=?",
                    (_json(row["suggestion"]), str(row["case_id"])),
                )
                if result.rowcount != 1:
                    raise ValueError(f"unknown S1 case_id in suggestions: {row['case_id']}")
                loaded += 1
        return {"loaded": loaded}

    def prioritize(self, username: str, case_ids: list[str]) -> dict[str, Any]:
        """Move these items to the front of the reviewer's queue, in this order; the rest keep their order."""
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            queue = [r["case_id"] for r in db.execute(
                "SELECT case_id FROM items WHERE reviewer_username=? ORDER BY queue_rank", (username,))]
            missing = [c for c in case_ids if c not in queue]
            if missing or len(set(case_ids)) != len(case_ids):
                raise ValueError(f"not in {username}'s queue or repeated: {missing or case_ids}")
            order = list(case_ids) + [c for c in queue if c not in set(case_ids)]
            offset = len(queue) + 1  # leave UNIQUE(reviewer, queue_rank) free while renumbering
            db.execute("UPDATE items SET queue_rank=queue_rank+? WHERE reviewer_username=?", (offset * 2, username))
            for rank, case_id in enumerate(order):
                db.execute("UPDATE items SET queue_rank=? WHERE case_id=?", (rank, case_id))
        return {"reviewer": username, "first": order[: len(case_ids)], "total": len(order)}

    def import_meta(self, rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
        loaded = 0
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for row in rows:
                case_id = str(row["case_id"])
                if not db.execute("SELECT 1 FROM items WHERE case_id=?", (case_id,)).fetchone():
                    raise ValueError(f"unknown S1 case_id in metadata: {case_id}")
                db.execute(
                    "INSERT INTO item_meta(case_id,dataset,human_versions_json) VALUES(?,?,?) "
                    "ON CONFLICT(case_id) DO UPDATE SET dataset=excluded.dataset,human_versions_json=excluded.human_versions_json",
                    (case_id, str(row["dataset"]), _json(sorted(row["human_versions"]))),
                )
                loaded += 1
        return {"loaded": loaded}

    def _task(self, row: sqlite3.Row, username: str) -> dict[str, Any]:
        payload = json.loads(row["payload_json"])
        answer = json.loads(row["answer_json"] or "{}")
        suggestion = json.loads(row["llm_suggestion_json"]) if row["llm_suggestion_json"] else None
        submitted = row["state"] == "submitted"
        if row["dataset"] is not None:
            payload["dataset"] = row["dataset"]
            # The human version is revealed only once the answer is submitted, and the answer is then locked.
            payload["reveal"] = {"human_versions": json.loads(row["human_versions_json"])} if submitted else None
        return payload | {
            "queue_rank": row["queue_rank"],
            "llm_suggestion": suggestion,
            "annotation": {"answer": answer, "state": row["state"] or "draft", "version": row["version"] or 0},
            "reviewer_username": username,
        }

    def get(self, case_id: str, username: str) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute(
                """SELECT i.*, a.answer_json, a.state, a.version, m.dataset, m.human_versions_json FROM items i
                   LEFT JOIN annotations a ON a.case_id=i.case_id LEFT JOIN item_meta m ON m.case_id=i.case_id
                   WHERE i.case_id=? AND i.reviewer_username=?""",
                (case_id, username),
            ).fetchone()
        if not row:
            raise KeyError(case_id)
        return self._task(row, username)

    def next(self, username: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                """SELECT i.*, a.answer_json, a.state, a.version, m.dataset, m.human_versions_json FROM items i
                   LEFT JOIN annotations a ON a.case_id=i.case_id LEFT JOIN item_meta m ON m.case_id=i.case_id
                   WHERE i.reviewer_username=? AND COALESCE(a.state,'draft')!='submitted'
                   ORDER BY i.queue_rank LIMIT 1""",
                (username,),
            ).fetchone()
        return self._task(row, username) if row else None

    def list_items(self, username: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                """SELECT i.case_id,i.axis,i.format,i.queue_rank,
                          COALESCE(a.state,'draft') state,COALESCE(a.version,0) version
                   FROM items i LEFT JOIN annotations a ON a.case_id=i.case_id
                   WHERE i.reviewer_username=? ORDER BY i.queue_rank""", (username,)
            ).fetchall()
        return [dict(row) for row in rows]

    def save(self, case_id: str, username: str, answer: Mapping[str, Any], expected_version: int, submit: bool) -> dict[str, Any]:
        now = _now()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            item = db.execute("SELECT 1 FROM items WHERE case_id=? AND reviewer_username=?", (case_id, username)).fetchone()
            if not item:
                raise KeyError(case_id)
            batch = db.execute("SELECT finished_at FROM batches WHERE reviewer_username=?", (username,)).fetchone()
            if batch and batch["finished_at"]:
                raise ValueError("the S1 batch is finished and can no longer be changed")
            old = db.execute("SELECT * FROM annotations WHERE case_id=?", (case_id,)).fetchone()
            revealed = db.execute("SELECT 1 FROM item_meta WHERE case_id=?", (case_id,)).fetchone()
            if old and old["state"] == "submitted" and revealed:
                raise ValueError("this answer is locked: the human version was shown after submission")
            old_version = int(old["version"]) if old else 0
            if old_version != expected_version:
                raise ValueError(f"stale S1 version: expected {expected_version}, current {old_version}")
            old_answer = old["answer_json"] if old else "{}"
            old_state = old["state"] if old else None
            new_state = "submitted" if submit else "draft"
            new_version = old_version + 1
            encoded = _json(dict(answer))
            db.execute(
                """INSERT INTO annotations(case_id,reviewer_username,state,answer_json,version,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET
                   state=excluded.state,answer_json=excluded.answer_json,version=excluded.version,updated_at=excluded.updated_at""",
                (case_id, username, new_state, encoded, new_version, now, now),
            )
            db.execute(
                "INSERT INTO revisions(case_id,reviewer_username,old_answer_json,new_answer_json,old_state,new_state,old_version,new_version,changed_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (case_id, username, old_answer, encoded, old_state, new_state, old_version, new_version, now),
            )
        return {"answer": dict(answer), "state": new_state, "version": new_version}

    def progress(self, username: str | None = None) -> dict[str, Any]:
        where, args = ("WHERE i.reviewer_username=?", (username,)) if username else ("", ())
        with self.connect() as db:
            rows = db.execute(
                f"""SELECT i.reviewer_username,COUNT(*) total,
                    SUM(CASE WHEN a.state='submitted' THEN 1 ELSE 0 END) done,
                    MAX(b.finished_at) finished_at FROM items i
                    LEFT JOIN annotations a ON a.case_id=i.case_id
                    LEFT JOIN batches b ON b.reviewer_username=i.reviewer_username
                    {where} GROUP BY i.reviewer_username""", args
            ).fetchall()
        return {"reviewers": [dict(row) for row in rows]}

    def finish(self, username: str) -> None:
        progress = self.progress(username)["reviewers"]
        if not progress or progress[0]["done"] != progress[0]["total"]:
            raise ValueError("all S1 items must be submitted before finishing the batch")
        with self.connect() as db:
            db.execute("UPDATE batches SET finished_at=? WHERE reviewer_username=?", (_now(), username))

    def export_rows(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                """SELECT i.*,a.answer_json,a.state,a.version,a.updated_at FROM items i
                   LEFT JOIN annotations a ON a.case_id=i.case_id ORDER BY i.reviewer_username,i.queue_rank"""
            ).fetchall()
        output = []
        for row in rows:
            suggestion = json.loads(row["llm_suggestion_json"]) if row["llm_suggestion_json"] else None
            final = json.loads(row["answer_json"]) if row["answer_json"] else None
            output.append({
                "case_id": row["case_id"], "axis": row["axis"], "format": row["format"],
                "reviewer_username": row["reviewer_username"], "queue_rank": row["queue_rank"],
                "is_control": bool(row["is_control"]), "control_kind": row["control_kind"],
                "state": row["state"] or "unstarted", "version": row["version"] or 0,
                "llm_suggestion": suggestion, "human_final": final,
                "changed": suggestion is not None and final is not None and any(
                    suggestion.get(key) != final.get(key)
                    for key in ("choice", "ranks", "side_effect", "side_effect_version")
                    if key in suggestion or key in final
                ),
                "updated_at": row["updated_at"],
            })
        return output

    def backup(self, output: Path) -> dict[str, str]:
        output.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, sqlite3.connect(output) as target:
            source.backup(target)
        return {"database": str(output)}
