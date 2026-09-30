"""SQLite persistence for the Phase 4a annotation campaign.

All write paths use ``BEGIN IMMEDIATE`` so task claims and optimistic annotation
updates remain atomic even when several linguists share one private server.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from .constants import (
    ANNOTATION_STATES,
    CAMPAIGN_ID,
    DEFAULT_LANGUAGE_PRIORITY,
    DEFAULT_LEASE_SECONDS,
    DEFAULT_MAX_ACTIVE_GAP_SECONDS,
    SCHEMA_VERSION,
    USER_ROLES,
)
from .errors import (
    AuthenticationError,
    BackendError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from .security import AuthenticatedUser, canonical_json, token_digest, verify_password


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class AnnotationDatabase:
    """Low-level campaign store with atomic queue and annotation operations."""

    def __init__(
        self,
        path: str | Path,
        *,
        campaign_id: str = CAMPAIGN_ID,
        language_priority: Sequence[str] = DEFAULT_LANGUAGE_PRIORITY,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        max_active_gap_seconds: int = DEFAULT_MAX_ACTIVE_GAP_SECONDS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.path = Path(path)
        self.campaign_id = campaign_id
        self.language_priority = tuple(language_priority)
        self.lease_seconds = lease_seconds
        self.max_active_gap_seconds = max_active_gap_seconds
        self._now_fn = now

    def _now(self) -> datetime:
        value = self._now_fn()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialise(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('reviewer', 'admin')),
                    allowed_languages_json TEXT,
                    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    csrf_token TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    canonical_pair_id TEXT NOT NULL,
                    language TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    target_text TEXT NOT NULL,
                    candidate_strategy TEXT NOT NULL,
                    source_tokens_json TEXT NOT NULL,
                    target_tokens_json TEXT NOT NULL,
                    simalign_links_json TEXT NOT NULL,
                    public_metadata_json TEXT NOT NULL,
                    model_votes_json TEXT NOT NULL,
                    queue_rank INTEGER NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (campaign_id, canonical_pair_id, candidate_strategy)
                );

                CREATE TABLE IF NOT EXISTS annotations (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id) ON DELETE RESTRICT,
                    reviewer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
                    state TEXT NOT NULL CHECK (state IN ('draft', 'submitted', 'skipped')),
                    version INTEGER NOT NULL CHECK (version >= 0),
                    verdict TEXT CHECK (verdict IN ('correct', 'incorrect', 'uncertain', 'skip')),
                    corrected_strategy TEXT,
                    source_evidence_json TEXT NOT NULL,
                    target_evidence_json TEXT NOT NULL,
                    alignment_judgments_json TEXT NOT NULL,
                    human_added_links_json TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    skip_reason TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    last_activity_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    submitted_at TEXT,
                    active_duration_seconds REAL NOT NULL DEFAULT 0 CHECK (active_duration_seconds >= 0)
                );

                CREATE TABLE IF NOT EXISTS leases (
                    task_id TEXT PRIMARY KEY REFERENCES tasks(task_id) ON DELETE CASCADE,
                    reviewer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    acquired_at TEXT NOT NULL,
                    renewed_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS annotation_revisions (
                    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE RESTRICT,
                    reviewer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
                    version INTEGER NOT NULL,
                    event TEXT NOT NULL,
                    state TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (task_id, version)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    actor_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
                    action TEXT NOT NULL,
                    task_id TEXT REFERENCES tasks(task_id) ON DELETE SET NULL,
                    annotation_version INTEGER,
                    request_id TEXT,
                    remote_addr TEXT,
                    details_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_queue
                    ON tasks(campaign_id, language, queue_rank, task_id);
                CREATE INDEX IF NOT EXISTS idx_annotations_reviewer_state
                    ON annotations(reviewer_id, state, updated_at);
                CREATE INDEX IF NOT EXISTS idx_annotations_state
                    ON annotations(state, task_id);
                CREATE INDEX IF NOT EXISTS idx_leases_expiry ON leases(expires_at);
                CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_events(task_id, event_id);
                """
            )
            # A schema-v1 database may have been created by an early Phase 4a
            # prototype.  This additive migration is safe and preserves its
            # revision history.
            annotation_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(annotations)")
            }
            if "skip_reason" not in annotation_columns:
                connection.execute(
                    "ALTER TABLE annotations ADD COLUMN skip_reason TEXT NOT NULL DEFAULT ''"
                )
            existing = connection.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            ).fetchone()
            if existing and int(existing["value"]) != SCHEMA_VERSION:
                raise RuntimeError(
                    f"database schema {existing['value']} is incompatible with {SCHEMA_VERSION}"
                )
            connection.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_meta(key, value) VALUES('campaign_id', ?)",
                (self.campaign_id,),
            )
            campaign = connection.execute(
                "SELECT value FROM schema_meta WHERE key = 'campaign_id'"
            ).fetchone()["value"]
            if campaign != self.campaign_id:
                raise RuntimeError(
                    f"database campaign {campaign!r} does not match configured {self.campaign_id!r}"
                )

    def backup(self, output: str | Path) -> dict[str, Any]:
        """Create a transactionally consistent SQLite backup."""
        destination_path = Path(output)
        if destination_path.resolve() == self.path.resolve():
            raise ValidationError(
                "backup output must differ from the live database"
            )
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source:
            destination = sqlite3.connect(destination_path)
            try:
                source.backup(destination)
            finally:
                destination.close()
        return {
            "database": str(self.path),
            "output": str(destination_path),
            "bytes": destination_path.stat().st_size,
        }

    @staticmethod
    def _decode_languages(value: str | None) -> tuple[str, ...] | None:
        if value is None:
            return None
        return tuple(json.loads(value))

    def create_or_update_user(
        self,
        *,
        username: str,
        display_name: str,
        password_hash: str,
        role: str,
        allowed_languages: Sequence[str] | None,
        active: bool = True,
        actor_user_id: int | None = None,
    ) -> dict[str, Any]:
        if role not in USER_ROLES:
            raise ValidationError(f"unknown user role: {role}")
        languages_json = None if allowed_languages is None else canonical_json(sorted(set(allowed_languages)))
        now = isoformat_utc(self._now())
        with self.transaction(immediate=True) as connection:
            existing = connection.execute(
                "SELECT user_id FROM users WHERE username = ? COLLATE NOCASE", (username,)
            ).fetchone()
            if existing:
                user_id = int(existing["user_id"])
                connection.execute(
                    """UPDATE users SET display_name=?, password_hash=?, role=?,
                       allowed_languages_json=?, active=?, updated_at=? WHERE user_id=?""",
                    (display_name, password_hash, role, languages_json, int(active), now, user_id),
                )
                action = "user.updated"
            else:
                cursor = connection.execute(
                    """INSERT INTO users(username, display_name, password_hash, role,
                       allowed_languages_json, active, created_at, updated_at)
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        username,
                        display_name,
                        password_hash,
                        role,
                        languages_json,
                        int(active),
                        now,
                        now,
                    ),
                )
                user_id = int(cursor.lastrowid)
                action = "user.created"
            self._audit(
                connection,
                actor_user_id=actor_user_id,
                action=action,
                details={"user_id": user_id, "username": username, "role": role},
                at=now,
            )
            row = connection.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return self._user_dict(row)

    def authenticate_password(self, username: str, password: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE AND active=1", (username,)
            ).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            return None
        return self._user_dict(row)

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE user_id=? AND active=1", (user_id,)
            ).fetchone()
        return self._user_dict(row) if row else None

    def _user_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "user_id": int(row["user_id"]),
            "username": row["username"],
            "display_name": row["display_name"],
            "role": row["role"],
            "allowed_languages": self._decode_languages(row["allowed_languages_json"]),
            "active": bool(row["active"]),
        }

    def create_session(
        self, *, user_id: int, token: str, csrf_token: str, expires_at: datetime
    ) -> None:
        now = isoformat_utc(self._now())
        with self.transaction(immediate=True) as connection:
            connection.execute(
                """INSERT INTO sessions(token_hash, user_id, csrf_token, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (token_digest(token), user_id, csrf_token, now, isoformat_utc(expires_at)),
            )
            self._audit(connection, actor_user_id=user_id, action="auth.login", at=now)

    def resolve_session(self, token: str) -> AuthenticatedUser | None:
        now = isoformat_utc(self._now())
        with self.connect() as connection:
            row = connection.execute(
                """SELECT s.csrf_token, u.* FROM sessions s
                   JOIN users u ON u.user_id=s.user_id
                   WHERE s.token_hash=? AND s.revoked_at IS NULL AND s.expires_at>?
                     AND u.active=1""",
                (token_digest(token), now),
            ).fetchone()
        if row is None:
            return None
        return AuthenticatedUser(
            user_id=int(row["user_id"]),
            username=row["username"],
            display_name=row["display_name"],
            role=row["role"],
            allowed_languages=self._decode_languages(row["allowed_languages_json"]),
            csrf_token=row["csrf_token"],
        )

    def revoke_session(self, token: str, *, actor_user_id: int) -> None:
        now = isoformat_utc(self._now())
        with self.transaction(immediate=True) as connection:
            connection.execute(
                "UPDATE sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",
                (now, token_digest(token)),
            )
            self._audit(connection, actor_user_id=actor_user_id, action="auth.logout", at=now)

    def audit_auth_failure(self, *, username: str, remote_addr: str | None) -> None:
        now = isoformat_utc(self._now())
        with self.transaction(immediate=True) as connection:
            self._audit(
                connection,
                action="auth.login_failed",
                details={"username": username},
                remote_addr=remote_addr,
                at=now,
            )

    def import_tasks(
        self, tasks: Iterable[Mapping[str, Any]], *, actor_user_id: int | None = None
    ) -> dict[str, int]:
        # Import is a trust boundary even when invoked from a maintenance CLI.
        from .validation import normalise_tasks

        validated_tasks = normalise_tasks(tasks)
        now = isoformat_utc(self._now())
        inserted = unchanged = 0
        with self.transaction(immediate=True) as connection:
            next_order = int(
                connection.execute(
                    "SELECT COALESCE(MAX(queue_rank), -1) + 1 AS value FROM tasks WHERE campaign_id=?",
                    (self.campaign_id,),
                ).fetchone()["value"]
            )
            for item in validated_tasks:
                queue_rank = item.get("queue_rank")
                if queue_rank is None:
                    queue_rank = next_order
                    next_order += 1
                values = (
                    item["task_id"],
                    self.campaign_id,
                    item["canonical_pair_id"],
                    item["language"],
                    canonical_json(item["sources"]),
                    item["source_text"],
                    item["target_text"],
                    item["candidate_strategy"],
                    canonical_json(item["source_tokens"]),
                    canonical_json(item["target_tokens"]),
                    canonical_json(item["simalign_links"]),
                    canonical_json(item.get("public_metadata", {})),
                    canonical_json(item.get("model_votes", {})),
                    int(queue_rank),
                    item["payload_hash"],
                    now,
                )
                existing = connection.execute(
                    "SELECT payload_hash FROM tasks WHERE task_id=?", (item["task_id"],)
                ).fetchone()
                if existing:
                    if existing["payload_hash"] != item["payload_hash"]:
                        raise ConflictError(
                            f"task {item['task_id']} already exists with different content"
                        )
                    unchanged += 1
                    continue
                try:
                    connection.execute(
                        """INSERT INTO tasks(
                           task_id, campaign_id, canonical_pair_id, language, sources_json,
                           source_text, target_text, candidate_strategy, source_tokens_json,
                           target_tokens_json, simalign_links_json, public_metadata_json,
                           model_votes_json, queue_rank, payload_hash, created_at)
                           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        values,
                    )
                except sqlite3.IntegrityError as error:
                    raise ConflictError(
                        "a task already represents this pair and candidate strategy",
                        details={
                            "task_id": item["task_id"],
                            "canonical_pair_id": item["canonical_pair_id"],
                            "candidate_strategy": item["candidate_strategy"],
                        },
                    ) from error
                inserted += 1
            self._audit(
                connection,
                actor_user_id=actor_user_id,
                action="tasks.imported",
                details={"inserted": inserted, "unchanged": unchanged},
                at=now,
            )
        return {"inserted": inserted, "unchanged": unchanged}

    @staticmethod
    def _allowed_clause(
        allowed_languages: Sequence[str] | None, *, column: str = "t.language"
    ) -> tuple[str, list[Any]]:
        if allowed_languages is None:
            return "", []
        if not allowed_languages:
            return " AND 0", []
        placeholders = ",".join("?" for _ in allowed_languages)
        return f" AND {column} IN ({placeholders})", list(allowed_languages)

    @staticmethod
    def _task_filter_clause(
        sources: Sequence[str], agreeing_models: Sequence[str]
    ) -> tuple[str, list[Any]]:
        sql = ""
        params: list[Any] = []
        if sources:
            placeholders = ",".join("?" for _ in sources)
            sql += (
                " AND EXISTS (SELECT 1 FROM json_each(t.sources_json) src "
                f"WHERE src.value IN ({placeholders}))"
            )
            params.extend(sources)
        for model in agreeing_models:
            sql += " AND json_extract(t.model_votes_json, ?) = 'yes'"
            params.append(f"$.{model}")
        return sql, params

    def claim_next(
        self,
        *,
        reviewer_id: int,
        allowed_languages: Sequence[str] | None,
        sources: Sequence[str] = (),
        agreeing_models: Sequence[str] = (),
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any] | None:
        now_dt = self._now()
        now = isoformat_utc(now_dt)
        expires = isoformat_utc(now_dt + timedelta(seconds=self.lease_seconds))
        allowed_sql, allowed_params = self._allowed_clause(allowed_languages)
        filter_sql, filter_params = self._task_filter_clause(sources, agreeing_models)
        language_case = "CASE " + " ".join(
            f"WHEN t.language=? THEN {index}" for index, _ in enumerate(self.language_priority)
        ) + f" ELSE {len(self.language_priority)} END"
        sql = f"""
            SELECT t.task_id
            FROM tasks t
            LEFT JOIN annotations a ON a.task_id=t.task_id
            LEFT JOIN leases l ON l.task_id=t.task_id AND l.expires_at>?
            WHERE t.campaign_id=?
              AND (a.task_id IS NULL OR (a.reviewer_id=? AND a.state IN ('draft', 'skipped')))
              AND (l.task_id IS NULL OR l.reviewer_id=?)
              {allowed_sql}
              {filter_sql}
            ORDER BY CASE
                         WHEN a.reviewer_id=? AND a.state='draft' THEN 0
                         WHEN a.task_id IS NULL THEN 1
                         ELSE 2
                     END,
                     {language_case}, t.language, t.queue_rank, t.task_id
            LIMIT 1
        """
        params: list[Any] = [now, self.campaign_id, reviewer_id, reviewer_id]
        params.extend(allowed_params)
        params.extend(filter_params)
        params.append(reviewer_id)
        params.extend(self.language_priority)
        with self.transaction(immediate=True) as connection:
            connection.execute("DELETE FROM leases WHERE expires_at<=?", (now,))
            row = connection.execute(sql, params).fetchone()
            if row is None:
                return None
            task_id = row["task_id"]
            annotation = connection.execute(
                "SELECT * FROM annotations WHERE task_id=?", (task_id,)
            ).fetchone()
            if annotation is None:
                connection.execute(
                    """INSERT INTO annotations(
                       task_id, reviewer_id, state, version, verdict, corrected_strategy,
                       source_evidence_json, target_evidence_json, alignment_judgments_json,
                       human_added_links_json, notes, skip_reason, started_at,
                       last_activity_at, updated_at,
                       submitted_at, active_duration_seconds)
                       VALUES(?, ?, 'draft', 0, NULL, NULL, '[]', '[]', '[]', '[]', '', '',
                              ?, ?, ?, NULL, 0)""",
                    (task_id, reviewer_id, now, now, now),
                )
                annotation = connection.execute(
                    "SELECT * FROM annotations WHERE task_id=?", (task_id,)
                ).fetchone()
                self._revision(connection, annotation, event="claimed", at=now)
            elif annotation["state"] == "skipped":
                version = int(annotation["version"]) + 1
                connection.execute(
                    """UPDATE annotations SET state='draft', version=?, verdict=NULL,
                       corrected_strategy=NULL, skip_reason='', last_activity_at=?,
                       updated_at=?, submitted_at=NULL WHERE task_id=?""",
                    (version, now, now, task_id),
                )
                annotation = connection.execute(
                    "SELECT * FROM annotations WHERE task_id=?", (task_id,)
                ).fetchone()
                self._revision(connection, annotation, event="deferred_resumed", at=now)
            connection.execute(
                """INSERT INTO leases(task_id, reviewer_id, acquired_at, renewed_at, expires_at)
                   VALUES(?, ?, ?, ?, ?)
                   ON CONFLICT(task_id) DO UPDATE SET reviewer_id=excluded.reviewer_id,
                   acquired_at=excluded.acquired_at, renewed_at=excluded.renewed_at,
                   expires_at=excluded.expires_at""",
                (task_id, reviewer_id, now, now, expires),
            )
            self._audit(
                connection,
                actor_user_id=reviewer_id,
                action="task.claimed",
                task_id=task_id,
                annotation_version=int(annotation["version"]),
                request_id=request_id,
                remote_addr=remote_addr,
                details={
                    "lease_expires_at": expires,
                    "source_filters": sorted(set(sources)),
                    "model_filters": sorted(set(agreeing_models)),
                    "review_mode": "visible_model_votes",
                },
                at=now,
            )
            return self._task_bundle(connection, task_id, include_model_votes=True)

    def get_task(
        self,
        task_id: str,
        *,
        user_id: int,
        role: str,
        allowed_languages: Sequence[str] | None,
        include_model_votes: bool = False,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            task = connection.execute("SELECT language FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if task is None:
                raise NotFoundError(f"task {task_id} was not found")
            if role != "admin" and allowed_languages is not None and task["language"] not in allowed_languages:
                raise PermissionDeniedError("this reviewer is not assigned to the task language")
            annotation = connection.execute(
                "SELECT reviewer_id FROM annotations WHERE task_id=?", (task_id,)
            ).fetchone()
            if role != "admin" and annotation and int(annotation["reviewer_id"]) != user_id:
                raise PermissionDeniedError("this task belongs to another reviewer")
            return self._task_bundle(
                connection, task_id, include_model_votes=include_model_votes
            )

    def list_mine(
        self, reviewer_id: int, *, states: Sequence[str] = ("draft", "skipped")
    ) -> list[dict[str, Any]]:
        unknown = set(states) - set(ANNOTATION_STATES)
        if unknown:
            raise ValidationError(f"unknown annotation states: {sorted(unknown)}")
        if not states:
            return []
        placeholders = ",".join("?" for _ in states)
        with self.connect() as connection:
            rows = connection.execute(
                f"""SELECT a.task_id, t.language, t.candidate_strategy, a.state, a.version,
                    a.updated_at, a.verdict, t.sources_json, t.source_text, t.target_text
                    FROM annotations a JOIN tasks t ON t.task_id=a.task_id
                    WHERE a.reviewer_id=? AND a.state IN ({placeholders})
                    ORDER BY a.updated_at DESC, a.task_id""",
                [reviewer_id, *states],
            ).fetchall()
        return [dict(row) for row in rows]

    def filter_options(
        self, allowed_languages: Sequence[str] | None
    ) -> dict[str, Any]:
        allowed_sql, allowed_params = self._allowed_clause(allowed_languages)
        with self.connect() as connection:
            rows = connection.execute(
                f"""SELECT DISTINCT src.value AS source
                    FROM tasks t, json_each(t.sources_json) src
                    WHERE t.campaign_id=? {allowed_sql}
                    ORDER BY src.value""",
                [self.campaign_id, *allowed_params],
            ).fetchall()
        return {
            "sources": [str(row["source"]) for row in rows],
            "anchor_model": "gemma",
            "models": ["qwen", "e5", "xlmr"],
        }

    def renew_lease(self, task_id: str, *, reviewer_id: int) -> dict[str, str]:
        now_dt = self._now()
        now = isoformat_utc(now_dt)
        expires = isoformat_utc(now_dt + timedelta(seconds=self.lease_seconds))
        with self.transaction(immediate=True) as connection:
            lease = connection.execute("SELECT * FROM leases WHERE task_id=?", (task_id,)).fetchone()
            if lease is None or int(lease["reviewer_id"]) != reviewer_id or lease["expires_at"] <= now:
                raise ConflictError("the task lease is missing or expired; resume the task")
            connection.execute(
                "UPDATE leases SET renewed_at=?, expires_at=? WHERE task_id=?",
                (now, expires, task_id),
            )
            self._audit(
                connection,
                actor_user_id=reviewer_id,
                action="lease.renewed",
                task_id=task_id,
                details={"lease_expires_at": expires},
                at=now,
            )
        return {"lease_expires_at": expires}

    def save_annotation(
        self,
        task_id: str,
        *,
        reviewer_id: int,
        expected_version: int,
        annotation: Mapping[str, Any],
        submit: bool = False,
        skip: bool = False,
        skip_reason: str | None = None,
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any]:
        now_dt = self._now()
        now = isoformat_utc(now_dt)
        new_state = "submitted" if submit else "skipped" if skip else "draft"
        event = "submitted" if submit else "skipped" if skip else "draft_saved"
        with self.transaction(immediate=True) as connection:
            current = connection.execute(
                "SELECT * FROM annotations WHERE task_id=?", (task_id,)
            ).fetchone()
            if current is None:
                raise NotFoundError("claim the task before saving an annotation")
            if int(current["reviewer_id"]) != reviewer_id:
                raise PermissionDeniedError("this task belongs to another reviewer")
            if current["state"] != "draft":
                raise ConflictError(f"cannot update an annotation in state {current['state']}")
            if int(current["version"]) != expected_version:
                raise ConflictError(
                    "annotation version is stale",
                    details={"expected_version": expected_version, "current_version": int(current["version"])},
                )
            lease = connection.execute("SELECT * FROM leases WHERE task_id=?", (task_id,)).fetchone()
            if lease is None or int(lease["reviewer_id"]) != reviewer_id or lease["expires_at"] <= now:
                raise ConflictError("the task lease is missing or expired; resume the task")
            task = connection.execute(
                """SELECT candidate_strategy, source_tokens_json, target_tokens_json, simalign_links_json
                   FROM tasks WHERE task_id=?""",
                (task_id,),
            ).fetchone()
            from .validation import normalise_annotation, validate_skip_reason

            merged = self._annotation_dict(current)
            for key in (
                "verdict",
                "corrected_strategy",
                "source_evidence",
                "target_evidence",
                "alignment_judgments",
                "human_added_links",
                "notes",
            ):
                if key in annotation:
                    merged[key] = annotation[key]
            clean = normalise_annotation(
                merged,
                source_tokens=json.loads(task["source_tokens_json"]),
                target_tokens=json.loads(task["target_tokens_json"]),
                simalign_links=json.loads(task["simalign_links_json"]),
                candidate_strategy=task["candidate_strategy"],
                final=submit,
            )
            clean_skip_reason = ""
            if skip:
                clean_skip_reason = validate_skip_reason(
                    skip_reason or annotation.get("skip_reason") or "unspecified"
                )
            elapsed = max(0.0, (now_dt - parse_utc(current["last_activity_at"])).total_seconds())
            duration = float(current["active_duration_seconds"]) + min(
                elapsed, float(self.max_active_gap_seconds)
            )
            version = expected_version + 1
            verdict = "skip" if skip else clean["verdict"]
            submitted_at = now if submit or skip else None
            connection.execute(
                """UPDATE annotations SET state=?, version=?, verdict=?, corrected_strategy=?,
                   source_evidence_json=?, target_evidence_json=?, alignment_judgments_json=?,
                   human_added_links_json=?, notes=?, skip_reason=?,
                   last_activity_at=?, updated_at=?,
                   submitted_at=?, active_duration_seconds=? WHERE task_id=?""",
                (
                    new_state,
                    version,
                    verdict,
                    clean["corrected_strategy"],
                    canonical_json(clean["source_evidence"]),
                    canonical_json(clean["target_evidence"]),
                    canonical_json(clean["alignment_judgments"]),
                    canonical_json(clean["human_added_links"]),
                    clean["notes"],
                    clean_skip_reason,
                    now,
                    now,
                    submitted_at,
                    duration,
                    task_id,
                ),
            )
            if submit or skip:
                connection.execute("DELETE FROM leases WHERE task_id=?", (task_id,))
            else:
                expires = isoformat_utc(now_dt + timedelta(seconds=self.lease_seconds))
                connection.execute(
                    "UPDATE leases SET renewed_at=?, expires_at=? WHERE task_id=?",
                    (now, expires, task_id),
                )
            updated = connection.execute(
                "SELECT * FROM annotations WHERE task_id=?", (task_id,)
            ).fetchone()
            self._revision(connection, updated, event=event, at=now)
            self._audit(
                connection,
                actor_user_id=reviewer_id,
                action=f"annotation.{event}",
                task_id=task_id,
                annotation_version=version,
                request_id=request_id,
                remote_addr=remote_addr,
                at=now,
            )
            return self._annotation_dict(updated)

    def resume(
        self,
        task_id: str,
        *,
        reviewer_id: int,
        role: str,
        expected_version: int,
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any]:
        now_dt = self._now()
        now = isoformat_utc(now_dt)
        expires = isoformat_utc(now_dt + timedelta(seconds=self.lease_seconds))
        with self.transaction(immediate=True) as connection:
            current = connection.execute(
                "SELECT * FROM annotations WHERE task_id=?", (task_id,)
            ).fetchone()
            if current is None:
                raise NotFoundError("the task has no annotation to resume")
            if int(current["reviewer_id"]) != reviewer_id and role != "admin":
                raise PermissionDeniedError("this task belongs to another reviewer")
            if int(current["version"]) != expected_version:
                raise ConflictError(
                    "annotation version is stale",
                    details={"expected_version": expected_version, "current_version": int(current["version"])},
                )
            active_lease = connection.execute(
                "SELECT * FROM leases WHERE task_id=? AND expires_at>?", (task_id, now)
            ).fetchone()
            if active_lease and int(active_lease["reviewer_id"]) != reviewer_id:
                raise ConflictError("the task is currently leased to another reviewer")
            owner_id = int(current["reviewer_id"])
            version = expected_version + 1
            if current["state"] == "submitted":
                connection.execute(
                    """UPDATE annotations SET state='draft', version=?,
                       last_activity_at=?, updated_at=?, submitted_at=NULL
                       WHERE task_id=?""",
                    (version, now, now, task_id),
                )
            else:
                connection.execute(
                    """UPDATE annotations SET state='draft', version=?, verdict=NULL,
                       corrected_strategy=NULL, skip_reason='', last_activity_at=?,
                       updated_at=?, submitted_at=NULL WHERE task_id=?""",
                    (version, now, now, task_id),
                )
            connection.execute(
                """INSERT INTO leases(task_id, reviewer_id, acquired_at, renewed_at, expires_at)
                   VALUES(?, ?, ?, ?, ?)
                   ON CONFLICT(task_id) DO UPDATE SET reviewer_id=excluded.reviewer_id,
                   acquired_at=excluded.acquired_at, renewed_at=excluded.renewed_at,
                   expires_at=excluded.expires_at""",
                (task_id, owner_id, now, now, expires),
            )
            updated = connection.execute(
                "SELECT * FROM annotations WHERE task_id=?", (task_id,)
            ).fetchone()
            self._revision(connection, updated, event="resumed", at=now)
            self._audit(
                connection,
                actor_user_id=reviewer_id,
                action="annotation.resumed",
                task_id=task_id,
                annotation_version=version,
                request_id=request_id,
                remote_addr=remote_addr,
                details={"lease_expires_at": expires},
                at=now,
            )
            return self._task_bundle(connection, task_id, include_model_votes=True)

    def _task_bundle(
        self, connection: sqlite3.Connection, task_id: str, *, include_model_votes: bool
    ) -> dict[str, Any]:
        row = connection.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"task {task_id} was not found")
        result: dict[str, Any] = {
            "task_id": row["task_id"],
            "campaign_id": row["campaign_id"],
            "canonical_pair_id": row["canonical_pair_id"],
            "language": row["language"],
            "sources": json.loads(row["sources_json"]),
            "source_text": row["source_text"],
            "target_text": row["target_text"],
            "candidate_strategy": row["candidate_strategy"],
            "source_tokens": json.loads(row["source_tokens_json"]),
            "target_tokens": json.loads(row["target_tokens_json"]),
            "simalign_links": json.loads(row["simalign_links_json"]),
            "metadata": self._blind_metadata(json.loads(row["public_metadata_json"])),
        }
        if include_model_votes:
            result["model_votes"] = json.loads(row["model_votes_json"])
        annotation = connection.execute(
            "SELECT * FROM annotations WHERE task_id=?", (task_id,)
        ).fetchone()
        result["annotation"] = self._annotation_dict(annotation) if annotation else None
        lease = connection.execute("SELECT * FROM leases WHERE task_id=?", (task_id,)).fetchone()
        result["lease"] = (
            {"reviewer_id": int(lease["reviewer_id"]), "expires_at": lease["expires_at"]}
            if lease
            else None
        )
        return result

    @staticmethod
    def _annotation_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "reviewer_id": int(row["reviewer_id"]),
            "state": row["state"],
            "version": int(row["version"]),
            "verdict": row["verdict"],
            "corrected_strategy": row["corrected_strategy"],
            "source_evidence": json.loads(row["source_evidence_json"]),
            "target_evidence": json.loads(row["target_evidence_json"]),
            "alignment_judgments": json.loads(row["alignment_judgments_json"]),
            "human_added_links": json.loads(row["human_added_links_json"]),
            "notes": row["notes"],
            "skip_reason": row["skip_reason"],
            "started_at": row["started_at"],
            "updated_at": row["updated_at"],
            "submitted_at": row["submitted_at"],
            "active_duration_seconds": float(row["active_duration_seconds"]),
        }

    def post_submit_result(self, task_id: str, *, reviewer_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                """SELECT t.sources_json, t.candidate_strategy, t.model_votes_json,
                          a.state, a.reviewer_id
                   FROM tasks t JOIN annotations a ON a.task_id=t.task_id
                   WHERE t.task_id=?""",
                (task_id,),
            ).fetchone()
            if row is None or int(row["reviewer_id"]) != reviewer_id:
                raise PermissionDeniedError("this task does not belong to the reviewer")
            if row["state"] != "submitted":
                raise ConflictError("model agreement is available only after submit")
            return {
                "sources": json.loads(row["sources_json"]),
                "candidate_strategy": row["candidate_strategy"],
                "model_votes": json.loads(row["model_votes_json"]),
            }

    @staticmethod
    def _blind_metadata(value: Any) -> Any:
        from .validation import blind_metadata

        return blind_metadata(value)

    def _revision(
        self, connection: sqlite3.Connection, row: sqlite3.Row, *, event: str, at: str
    ) -> None:
        snapshot = self._annotation_dict(row)
        connection.execute(
            """INSERT INTO annotation_revisions(
               task_id, reviewer_id, version, event, state, snapshot_json, created_at)
               VALUES(?, ?, ?, ?, ?, ?, ?)""",
            (
                row["task_id"],
                row["reviewer_id"],
                row["version"],
                event,
                row["state"],
                canonical_json(snapshot),
                at,
            ),
        )

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        *,
        action: str,
        at: str,
        actor_user_id: int | None = None,
        task_id: str | None = None,
        annotation_version: int | None = None,
        request_id: str | None = None,
        remote_addr: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        connection.execute(
            """INSERT INTO audit_events(created_at, actor_user_id, action, task_id,
               annotation_version, request_id, remote_addr, details_json)
               VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                at,
                actor_user_id,
                action,
                task_id,
                annotation_version,
                request_id,
                remote_addr,
                canonical_json(details or {}),
            ),
        )

    def progress(self) -> dict[str, Any]:
        now = isoformat_utc(self._now())
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT t.task_id, t.language, t.sources_json, t.candidate_strategy,
                   a.state, a.verdict, a.reviewer_id,
                   CASE WHEN l.expires_at>? THEN 1 ELSE 0 END AS actively_leased
                   FROM tasks t
                   LEFT JOIN annotations a ON a.task_id=t.task_id
                   LEFT JOIN leases l ON l.task_id=t.task_id
                   WHERE t.campaign_id=? ORDER BY t.task_id""",
                (now, self.campaign_id),
            ).fetchall()
            users = connection.execute(
                """SELECT u.user_id, u.username, u.display_name, u.allowed_languages_json,
                   COUNT(a.task_id) AS touched,
                   SUM(CASE WHEN a.state='submitted' THEN 1 ELSE 0 END) AS submitted,
                   SUM(CASE WHEN a.state='skipped' THEN 1 ELSE 0 END) AS skipped,
                   SUM(CASE WHEN a.state='draft' THEN 1 ELSE 0 END) AS draft
                   FROM users u LEFT JOIN annotations a ON a.reviewer_id=u.user_id
                   WHERE u.role='reviewer' GROUP BY u.user_id ORDER BY u.username"""
            ).fetchall()
        dimensions: dict[str, dict[str, dict[str, int]]] = {
            "language": {},
            "source": {},
            "strategy": {},
        }
        totals = {"total": 0, "unstarted": 0, "draft": 0, "submitted": 0, "skipped": 0, "leased": 0}

        def update_dimension(dimension: str, key: str, state: str, leased: bool) -> None:
            bucket = dimensions[dimension].setdefault(
                key,
                {"total": 0, "unstarted": 0, "draft": 0, "submitted": 0, "skipped": 0, "leased": 0},
            )
            bucket["total"] += 1
            bucket[state] += 1
            if leased:
                bucket["leased"] += 1

        for row in rows:
            state = row["state"] or "unstarted"
            leased = bool(row["actively_leased"])
            totals["total"] += 1
            totals[state] += 1
            if leased:
                totals["leased"] += 1
            update_dimension("language", row["language"], state, leased)
            update_dimension("strategy", row["candidate_strategy"], state, leased)
            for source in json.loads(row["sources_json"]):
                update_dimension("source", source, state, leased)
        reviewers = [
            {
                "user_id": int(row["user_id"]),
                "username": row["username"],
                "display_name": row["display_name"],
                "allowed_languages": self._decode_languages(row["allowed_languages_json"]),
                "touched": int(row["touched"] or 0),
                "draft": int(row["draft"] or 0),
                "submitted": int(row["submitted"] or 0),
                "skipped": int(row["skipped"] or 0),
            }
            for row in users
        ]
        return {
            "campaign_id": self.campaign_id,
            "generated_at": now,
            "totals": totals,
            "by_language": dimensions["language"],
            "by_source": dimensions["source"],
            "by_strategy": dimensions["strategy"],
            "reviewers": reviewers,
        }

    def reviewer_progress(
        self,
        reviewer_id: int,
        *,
        allowed_languages: Sequence[str] | None,
        sources: Sequence[str] = (),
        agreeing_models: Sequence[str] = (),
    ) -> dict[str, Any]:
        """Return progress for one reviewer without leaking other annotations."""

        allowed_sql, allowed_params = self._allowed_clause(allowed_languages)
        filter_sql, filter_params = self._task_filter_clause(sources, agreeing_models)
        with self.connect() as connection:
            rows = connection.execute(
                f"""SELECT t.language, a.reviewer_id, a.state
                    FROM tasks t
                    LEFT JOIN annotations a ON a.task_id=t.task_id
                    WHERE t.campaign_id=? {allowed_sql} {filter_sql}
                    ORDER BY t.language, t.queue_rank, t.task_id""",
                [self.campaign_id, *allowed_params, *filter_params],
            ).fetchall()
        by_language: dict[str, dict[str, int]] = {}
        totals = {
            "total": 0,
            "completed": 0,
            "remaining": 0,
            "submitted": 0,
            "skipped": 0,
            "draft": 0,
            "unavailable": 0,
        }
        for row in rows:
            bucket = by_language.setdefault(
                row["language"],
                {
                    "total": 0,
                    "completed": 0,
                    "remaining": 0,
                    "submitted": 0,
                    "skipped": 0,
                    "draft": 0,
                    "unavailable": 0,
                },
            )
            for target in (totals, bucket):
                target["total"] += 1
            owner = int(row["reviewer_id"]) if row["reviewer_id"] is not None else None
            if owner is not None and owner != reviewer_id:
                totals["unavailable"] += 1
                bucket["unavailable"] += 1
                continue
            state = row["state"]
            if state in {"submitted", "skipped"}:
                totals["completed"] += 1
                bucket["completed"] += 1
                totals[state] += 1
                bucket[state] += 1
            else:
                totals["remaining"] += 1
                bucket["remaining"] += 1
                if state == "draft":
                    totals["draft"] += 1
                    bucket["draft"] += 1
        return {
            "campaign_id": self.campaign_id,
            **totals,
            "by_language": {key: by_language[key] for key in sorted(by_language)},
        }

    def iter_export_rows(self, *, include_model_votes: bool = True) -> Iterator[dict[str, Any]]:
        language_rank = {language: rank for rank, language in enumerate(self.language_priority)}
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT t.*, a.*, u.username, u.display_name
                   FROM tasks t
                   LEFT JOIN annotations a ON a.task_id=t.task_id
                   LEFT JOIN users u ON u.user_id=a.reviewer_id
                   WHERE t.campaign_id=?""",
                (self.campaign_id,),
            ).fetchall()
        ordered = sorted(
            rows,
            key=lambda row: (
                language_rank.get(row["language"], len(language_rank)),
                row["language"],
                int(row["queue_rank"]),
                row["task_id"],
            ),
        )
        for row in ordered:
            source_tokens = json.loads(row["source_tokens_json"])
            target_tokens = json.loads(row["target_tokens_json"])
            source_evidence = json.loads(row["source_evidence_json"]) if row["state"] else []
            target_evidence = json.loads(row["target_evidence_json"]) if row["state"] else []
            record: dict[str, Any] = {
                "export_schema": "feats-phase4a-annotation-v1",
                "campaign_id": row["campaign_id"],
                "task_id": row["task_id"],
                "canonical_pair_id": row["canonical_pair_id"],
                "language": row["language"],
                "sources": json.loads(row["sources_json"]),
                "source_text": row["source_text"],
                "target_text": row["target_text"],
                "candidate_strategy": row["candidate_strategy"],
                "annotation_state": row["state"] or "unstarted",
                "verdict": row["verdict"],
                "corrected_strategy": row["corrected_strategy"],
                "annotation_version": int(row["version"]) if row["state"] else None,
                "reviewer_username": row["username"],
                "reviewer_display_name": row["display_name"],
                "source_evidence": self._enrich_evidence(source_evidence, source_tokens),
                "target_evidence": self._enrich_evidence(target_evidence, target_tokens),
                "alignment_judgments": (
                    json.loads(row["alignment_judgments_json"]) if row["state"] else []
                ),
                "human_added_links": (
                    json.loads(row["human_added_links_json"]) if row["state"] else []
                ),
                "notes": row["notes"] if row["state"] else "",
                "skip_reason": row["skip_reason"] if row["state"] else "",
                "simalign_links": json.loads(row["simalign_links_json"]),
                "started_at": row["started_at"],
                "updated_at": row["updated_at"],
                "submitted_at": row["submitted_at"],
                "active_duration_seconds": (
                    float(row["active_duration_seconds"]) if row["state"] else 0.0
                ),
            }
            if include_model_votes:
                record["model_votes"] = json.loads(row["model_votes_json"])
            yield record

    @staticmethod
    def _enrich_evidence(
        selections: Sequence[Mapping[str, Any]], tokens: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        by_index = {int(token["index"]): token for token in tokens}
        enriched = []
        for selection in sorted(selections, key=lambda item: (int(item["token_index"]), item["role"])):
            token = by_index.get(int(selection["token_index"]), {})
            enriched.append(
                {
                    "token_index": int(selection["token_index"]),
                    "role": selection["role"],
                    "text": token.get("text"),
                    "upos": token.get("upos"),
                    "xpos": token.get("xpos"),
                }
            )
            enriched[-1].update({key: token.get(key) for key in ("start", "end", "orthographic_parent_index", "sentence_id", "sentence_token_index", "lemma", "feats", "head_index", "deprel", "parse_status")})
        return enriched

    def revisions(self, task_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT revision_id, reviewer_id, version, event, state,
                   snapshot_json, created_at FROM annotation_revisions
                   WHERE task_id=? ORDER BY version""",
                (task_id,),
            ).fetchall()
        return [
            {
                "revision_id": int(row["revision_id"]),
                "reviewer_id": int(row["reviewer_id"]),
                "version": int(row["version"]),
                "event": row["event"],
                "state": row["state"],
                "snapshot": json.loads(row["snapshot_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def audit_events(
        self, *, task_id: str | None = None, limit: int = 1_000
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 10_000:
            raise ValidationError("audit limit must be between 1 and 10000")
        where = "WHERE e.task_id=?" if task_id is not None else ""
        params: list[Any] = [task_id] if task_id is not None else []
        params.append(limit)
        with self.connect() as connection:
            rows = connection.execute(
                f"""SELECT e.*, u.username
                    FROM audit_events e
                    LEFT JOIN users u ON u.user_id=e.actor_user_id
                    {where}
                    ORDER BY e.event_id DESC LIMIT ?""",
                params,
            ).fetchall()
        return [
            {
                "event_id": int(row["event_id"]),
                "created_at": row["created_at"],
                "actor_user_id": (
                    int(row["actor_user_id"]) if row["actor_user_id"] is not None else None
                ),
                "actor_username": row["username"],
                "action": row["action"],
                "task_id": row["task_id"],
                "annotation_version": row["annotation_version"],
                "request_id": row["request_id"],
                "remote_addr": row["remote_addr"],
                "details": json.loads(row["details_json"]),
            }
            for row in rows
        ]
