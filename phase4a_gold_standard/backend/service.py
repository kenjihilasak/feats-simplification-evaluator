"""Application service joining authentication, policy, and persistence."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .constants import (
    CAMPAIGN_ID,
    DEFAULT_LANGUAGE_PRIORITY,
    DEFAULT_LEASE_SECONDS,
    DEFAULT_MAX_ACTIVE_GAP_SECONDS,
    DEFAULT_SESSION_SECONDS,
)
from .database import AnnotationDatabase
from .errors import (
    AuthenticationError,
    PermissionDeniedError,
    ValidationError,
)
from .reports import build_report, render_csv, render_jsonl
from .security import (
    AuthenticatedUser,
    hash_password,
    new_csrf_token,
    new_session_token,
)
from .validation import validate_skip_reason


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ServiceSettings:
    database_path: Path = Path("phase4a_gold_standard/runtime/annotations.sqlite3")
    session_secret: str = field(default_factory=lambda: secrets.token_urlsafe(48))
    campaign_id: str = CAMPAIGN_ID
    language_priority: tuple[str, ...] = DEFAULT_LANGUAGE_PRIORITY
    lease_seconds: int = DEFAULT_LEASE_SECONDS
    session_seconds: int = DEFAULT_SESSION_SECONDS
    max_active_gap_seconds: int = DEFAULT_MAX_ACTIVE_GAP_SECONDS
    session_cookie: str = "phase4a_session"
    csrf_cookie: str = "phase4a_csrf"
    cookie_secure: bool = False

    @classmethod
    def from_env(cls) -> "ServiceSettings":
        languages = tuple(
            value.strip().lower()
            for value in os.environ.get(
                "PHASE4A_LANGUAGE_PRIORITY", ",".join(DEFAULT_LANGUAGE_PRIORITY)
            ).split(",")
            if value.strip()
        )
        return cls(
            database_path=Path(
                os.environ.get(
                    "PHASE4A_DATABASE",
                    "phase4a_gold_standard/runtime/annotations.sqlite3",
                )
            ),
            session_secret=os.environ.get(
                "PHASE4A_SESSION_SECRET", secrets.token_urlsafe(48)
            ),
            campaign_id=os.environ.get("PHASE4A_CAMPAIGN_ID", CAMPAIGN_ID),
            language_priority=languages,
            lease_seconds=int(
                os.environ.get("PHASE4A_LEASE_SECONDS", DEFAULT_LEASE_SECONDS)
            ),
            session_seconds=int(
                os.environ.get("PHASE4A_SESSION_SECONDS", DEFAULT_SESSION_SECONDS)
            ),
            max_active_gap_seconds=int(
                os.environ.get(
                    "PHASE4A_MAX_ACTIVE_GAP_SECONDS",
                    DEFAULT_MAX_ACTIVE_GAP_SECONDS,
                )
            ),
            session_cookie=os.environ.get(
                "PHASE4A_SESSION_COOKIE", "phase4a_session"
            ),
            csrf_cookie=os.environ.get("PHASE4A_CSRF_COOKIE", "phase4a_csrf"),
            cookie_secure=_env_bool("PHASE4A_COOKIE_SECURE", False),
        )


class AnnotationService:
    def __init__(
        self,
        settings: ServiceSettings | None = None,
        *,
        database: AnnotationDatabase | None = None,
    ) -> None:
        self.settings = settings or ServiceSettings.from_env()
        self.database = database or AnnotationDatabase(
            self.settings.database_path,
            campaign_id=self.settings.campaign_id,
            language_priority=self.settings.language_priority,
            lease_seconds=self.settings.lease_seconds,
            max_active_gap_seconds=self.settings.max_active_gap_seconds,
        )
        self.database.initialise()

    @staticmethod
    def user_payload(user: AuthenticatedUser | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(user, AuthenticatedUser):
            return {
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
                "allowed_languages": (
                    list(user.allowed_languages)
                    if user.allowed_languages is not None
                    else None
                ),
            }
        return {
            "user_id": int(user["user_id"]),
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
            "allowed_languages": (
                list(user["allowed_languages"])
                if user.get("allowed_languages") is not None
                else None
            ),
        }

    def create_user(
        self,
        *,
        username: str,
        display_name: str,
        password: str,
        role: str = "reviewer",
        allowed_languages: Sequence[str] | None = None,
        active: bool = True,
        actor: AuthenticatedUser | None = None,
    ) -> dict[str, Any]:
        if actor is not None:
            self.require_admin(actor)
        username = username.strip()
        display_name = display_name.strip()
        if not username or len(username) > 100:
            raise ValidationError("username must contain 1 to 100 characters")
        if not display_name or len(display_name) > 200:
            raise ValidationError("display_name must contain 1 to 200 characters")
        languages = (
            None
            if allowed_languages is None
            else tuple(
                sorted(
                    {
                        str(language).strip().lower()
                        for language in allowed_languages
                        if str(language).strip()
                    }
                )
            )
        )
        if role == "reviewer" and not languages:
            raise ValidationError("reviewer accounts require at least one allowed language")
        return self.database.create_or_update_user(
            username=username,
            display_name=display_name,
            password_hash=hash_password(password),
            role=role,
            allowed_languages=languages,
            active=active,
            actor_user_id=actor.user_id if actor else None,
        )

    def login(
        self, username: str, password: str, *, remote_addr: str | None = None
    ) -> tuple[str, AuthenticatedUser]:
        user = self.database.authenticate_password(username, password)
        if user is None:
            self.database.audit_auth_failure(username=username, remote_addr=remote_addr)
            raise AuthenticationError("invalid username or password")
        token = new_session_token()
        csrf_token = new_csrf_token()
        self.database.create_session(
            user_id=int(user["user_id"]),
            token=token,
            csrf_token=csrf_token,
            expires_at=self.database._now()
            + timedelta(seconds=self.settings.session_seconds),
        )
        authenticated = AuthenticatedUser(
            user_id=int(user["user_id"]),
            username=str(user["username"]),
            display_name=str(user["display_name"]),
            role=str(user["role"]),
            allowed_languages=user["allowed_languages"],
            csrf_token=csrf_token,
        )
        return token, authenticated

    def resolve_session(self, token: str) -> AuthenticatedUser:
        user = self.database.resolve_session(token)
        if user is None:
            raise AuthenticationError("the session is missing, expired, or invalid")
        return user

    def logout(self, token: str, user: AuthenticatedUser) -> None:
        self.database.revoke_session(token, actor_user_id=user.user_id)

    @staticmethod
    def require_admin(user: AuthenticatedUser) -> None:
        if user.role != "admin":
            raise PermissionDeniedError("administrator access is required")

    @staticmethod
    def require_reviewer(user: AuthenticatedUser) -> None:
        if user.role != "reviewer":
            raise PermissionDeniedError("reviewer access is required")

    def import_tasks(
        self, records: Iterable[Mapping[str, Any]], *, actor: AuthenticatedUser | None = None
    ) -> dict[str, int]:
        if actor is not None:
            self.require_admin(actor)
        return self.database.import_tasks(
            records, actor_user_id=actor.user_id if actor else None
        )

    def claim_next(
        self,
        user: AuthenticatedUser,
        *,
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any] | None:
        self.require_reviewer(user)
        return self.database.claim_next(
            reviewer_id=user.user_id,
            allowed_languages=user.allowed_languages,
            request_id=request_id,
            remote_addr=remote_addr,
        )

    def get_task(self, task_id: str, user: AuthenticatedUser) -> dict[str, Any]:
        return self.database.get_task(
            task_id,
            user_id=user.user_id,
            role=user.role,
            allowed_languages=user.allowed_languages,
            include_model_votes=False,
        )

    def save(
        self,
        task_id: str,
        user: AuthenticatedUser,
        *,
        annotation: Mapping[str, Any],
        expected_version: int,
        submit: bool = False,
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any]:
        self.require_reviewer(user)
        return self.database.save_annotation(
            task_id,
            reviewer_id=user.user_id,
            expected_version=expected_version,
            annotation=annotation,
            submit=submit,
            request_id=request_id,
            remote_addr=remote_addr,
        )

    def skip(
        self,
        task_id: str,
        user: AuthenticatedUser,
        *,
        reason: str,
        notes: str | None,
        expected_version: int,
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any]:
        self.require_reviewer(user)
        clean_reason = validate_skip_reason(reason)
        patch: dict[str, Any] = {}
        if notes is not None:
            patch["notes"] = notes
        return self.database.save_annotation(
            task_id,
            reviewer_id=user.user_id,
            expected_version=expected_version,
            annotation=patch,
            skip=True,
            skip_reason=clean_reason,
            request_id=request_id,
            remote_addr=remote_addr,
        )

    def resume(
        self,
        task_id: str,
        user: AuthenticatedUser,
        *,
        expected_version: int,
        request_id: str | None = None,
        remote_addr: str | None = None,
    ) -> dict[str, Any]:
        self.get_task(task_id, user)
        return self.database.resume(
            task_id,
            reviewer_id=user.user_id,
            role=user.role,
            expected_version=expected_version,
            request_id=request_id,
            remote_addr=remote_addr,
        )

    def my_progress(self, user: AuthenticatedUser) -> dict[str, Any]:
        return self.database.reviewer_progress(
            user.user_id, allowed_languages=user.allowed_languages
        )

    def admin_progress(self, user: AuthenticatedUser) -> dict[str, Any]:
        self.require_admin(user)
        return self.database.progress()

    def export(self, user: AuthenticatedUser, *, format: str = "jsonl") -> str:
        self.require_admin(user)
        records = list(self.database.iter_export_rows(include_model_votes=True))
        if format == "jsonl":
            return render_jsonl(records)
        if format == "csv":
            return render_csv(records)
        raise ValidationError("export format must be jsonl or csv")

    def report(self, user: AuthenticatedUser) -> dict[str, Any]:
        self.require_admin(user)
        records = list(self.database.iter_export_rows(include_model_votes=True))
        return build_report(records, progress=self.database.progress())

    def revisions(self, task_id: str, user: AuthenticatedUser) -> list[dict[str, Any]]:
        self.require_admin(user)
        self.database.get_task(
            task_id,
            user_id=user.user_id,
            role=user.role,
            allowed_languages=None,
        )
        return self.database.revisions(task_id)

    def audit(
        self,
        user: AuthenticatedUser,
        *,
        task_id: str | None = None,
        limit: int = 1_000,
    ) -> list[dict[str, Any]]:
        self.require_admin(user)
        return self.database.audit_events(task_id=task_id, limit=limit)
