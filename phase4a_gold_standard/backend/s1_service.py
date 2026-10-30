"""Policy and validation for the S1 degradation-validation module (English, Spanish, French and Italian)."""

from __future__ import annotations

import re
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .errors import PermissionDeniedError, ValidationError
from .security import AuthenticatedUser
from .s1_database import S1Database

FORBIDDEN_PUBLIC_FIELDS = {"level", "levels", "operation", "operations", "generator", "pair_id", "canonical_pair_id"}
AXES = {"MEANING", "FLUENCY", "MOD", "OMIT", "SYN", "EXPL", "ILLOC", "COMP", "SYNT"}
LANGUAGES = {"en", "es", "fr", "it"}


@dataclass(frozen=True)
class S1Settings:
    database_path: Path = Path("phase4a_gold_standard/runtime/s1_validation_v1.sqlite3")

    @classmethod
    def from_env(cls) -> "S1Settings":
        return cls(Path(os.environ.get("S1_DATABASE", "phase4a_gold_standard/runtime/s1_validation_v1.sqlite3")))


def _forbidden(value: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if str(key).lower() in FORBIDDEN_PUBLIC_FIELDS:
                found.append(child_path)
            found.extend(_forbidden(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_forbidden(child, f"{path}[{index}]"))
    return found


class S1Service:
    def __init__(self, settings: S1Settings | None = None) -> None:
        self.settings = settings or S1Settings.from_env()
        self.database = S1Database(self.settings.database_path)
        self.database.initialise()

    @staticmethod
    def require_access(user: AuthenticatedUser) -> None:
        if user.role == "admin":
            return
        if user.role != "reviewer" or user.allowed_languages is None or not LANGUAGES & set(user.allowed_languages):
            raise PermissionDeniedError("S1 is available only to English, Spanish and French reviewers and administrators")

    @staticmethod
    def _require_language(task: Mapping[str, Any] | None, user: AuthenticatedUser) -> None:
        """An item is shown only to a reviewer allowed its language (English items predate the field)."""
        if task is not None and user.role != "admin" and task.get("language", "en") not in (user.allowed_languages or ()):
            raise PermissionDeniedError("this S1 item is in a language the reviewer is not assigned")

    def import_items(self, records: Iterable[Mapping[str, Any]], reviewer: str) -> dict[str, int]:
        clean = []
        for record in records:
            item = dict(record)
            bad = _forbidden(item)
            if bad:
                raise ValidationError(f"hidden S1 fields are forbidden: {bad}")
            if item.get("axis") not in AXES or item.get("format") not in {"pair", "rank3"}:
                raise ValidationError(f"invalid S1 item {item.get('case_id')}")
            if item.get("language", "en") not in LANGUAGES:
                raise ValidationError(f"unsupported S1 language for {item.get('case_id')}")
            labels = set(item.get("versions", {}))
            expected = {"X", "Y"} if item["format"] == "pair" else {"X", "Y", "Z"}
            if labels != expected:
                raise ValidationError(f"invalid versions for {item.get('case_id')}")
            clean.append(item)
        return self.database.import_items(clean, reviewer)

    def task(self, case_id: str, user: AuthenticatedUser) -> dict[str, Any]:
        self.require_access(user)
        try:
            task = self.database.get(case_id, user.username)
        except KeyError as error:
            raise PermissionDeniedError("S1 item is not assigned to this reviewer") from error
        self._require_language(task, user)
        return task

    def next(self, user: AuthenticatedUser) -> dict[str, Any] | None:
        self.require_access(user)
        task = self.database.next(user.username)
        self._require_language(task, user)
        return task

    def save(self, case_id: str, user: AuthenticatedUser, answer: Mapping[str, Any], version: int, submit: bool) -> dict[str, Any]:
        self.require_access(user)
        task = self.task(case_id, user)
        self._validate_answer(task, answer, submit)
        try:
            return self.database.save(case_id, user.username, answer, version, submit)
        except ValueError as error:
            raise ValidationError(str(error)) from error

    @staticmethod
    def _validate_answer(task: Mapping[str, Any], answer: Mapping[str, Any], submit: bool) -> None:
        if len(str(answer.get("note", ""))) > 4000:
            raise ValidationError("S1 note is too long")
        if len(str(answer.get("rationale", ""))) > 4000:
            raise ValidationError("S1 rationale is too long")
        if not submit:
            return
        selected = answer.get("selected_original_words")
        if not isinstance(selected, list) or not selected:
            raise ValidationError("select at least one affected word in the original sentence")
        if len(selected) > 500:
            raise ValidationError("too many selected original words")
        original = str(task["original"])
        words = [(m.start(), m.end(), m.group()) for m in re.finditer(r"[^\W_]+(?:['’\-][^\W_]+)*", original, re.UNICODE)]
        seen: set[int] = set()
        for word in selected:
            if not isinstance(word, dict) or set(word) != {"index", "start", "end", "text"}:
                raise ValidationError("selected original words have an invalid shape")
            index, start, end, text = word["index"], word["start"], word["end"], word["text"]
            if any(isinstance(value, bool) or not isinstance(value, int) for value in (index, start, end)):
                raise ValidationError("selected original word positions must be integers")
            if index < 0 or index in seen or start < 0 or end <= start or end > len(original):
                raise ValidationError("selected original word positions are invalid")
            if not isinstance(text, str) or original[start:end] != text or not text.strip():
                raise ValidationError("selected original word text does not match the sentence")
            if index >= len(words) or words[index] != (start, end, text):
                raise ValidationError("selected original word does not match its token index")
            seen.add(index)
        if task["format"] == "pair" and answer.get("choice") not in {"X", "Y", "Same", "SameBad"}:
            raise ValidationError("choose X, Y, Same (equally good), or SameBad (equally bad)")
        if task["format"] == "rank3":
            ranks = answer.get("ranks")
            if not isinstance(ranks, dict) or set(ranks) != {"X", "Y", "Z"} or any(ranks[x] not in {1, 2, 3} for x in ranks):
                raise ValidationError("assign rank 1, 2, or 3 to X, Y, and Z; equal ranks indicate ties")
        if "side_effects" in answer:
            effects, versions = answer.get("side_effects"), answer.get("side_effect_versions")
            if not isinstance(effects, list) or not effects or not (effects == ["none"] or set(effects) <= {"meaning", "fluency", "other"}):
                raise ValidationError("answer the side-effect question: No, or one or more side effects")
            if effects != ["none"]:
                if not isinstance(versions, list) or not versions or not set(versions) <= set(task["versions"]):
                    raise ValidationError("identify which version or versions have the side effect")
                if "other" in effects and not str(answer.get("side_effect_other", "")).strip():
                    raise ValidationError("describe the other side effect")
            if len(str(answer.get("side_effect_other", ""))) > 500:
                raise ValidationError("the side-effect description is too long")
            return
        if answer.get("side_effect") not in {"none", "meaning", "fluency", "other"}:
            raise ValidationError("answer the side-effect question")
        if answer.get("side_effect") != "none" and answer.get("side_effect_version") not in set(task["versions"]):
            raise ValidationError("identify which version has the side effect")

