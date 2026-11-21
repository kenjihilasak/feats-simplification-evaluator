"""Read-only audit: did reviewers meet S1 items whose word selection the old server rejected?

Before 21 Nov 2026 the server split words on Python's \\w, which excludes combining marks, while the page keeps
them inside the word ("Jose" + U+0301 is one word on the page, two on the server). Selecting a word at or after
such an accent was rejected on submit. This lists every such item a reviewer has touched and what happened.

    python -m phase4a_gold_standard.backend.s1_token_audit /data/s1_validation_v1.sqlite3
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata

OLD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)


def _word_char(c: str) -> bool:
    return unicodedata.category(c)[0] in "LMN"


def page_words(text: str) -> list[tuple[int, int, str]]:
    """The page's tokenisation (s1.js); identical to backend.s1_service.original_words."""
    words, i, n = [], 0, len(text)
    while i < n:
        if not _word_char(text[i]):
            i += 1
            continue
        start = i
        while i < n and _word_char(text[i]):
            i += 1
        while i + 1 < n and text[i] in "'’-" and _word_char(text[i + 1]):
            i += 1
            while i < n and _word_char(text[i]):
                i += 1
        words.append((start, i, text[start:i]))
    return words


def old_words(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group()) for m in OLD.finditer(text)]


def rejected(answer: dict, old: list) -> list[str]:
    """Selected words the old server would have refused."""
    out = []
    for w in answer.get("selected_original_words") or []:
        i = w.get("index")
        if not isinstance(i, int) or i >= len(old) or old[i] != (w.get("start"), w.get("end"), w.get("text")):
            out.append(str(w.get("text")))
    return out


def main(path: str) -> None:
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    items = db.execute(
        """SELECT i.case_id, i.reviewer_username, i.queue_rank, i.payload_json, a.state, a.answer_json, a.updated_at
           FROM items i LEFT JOIN annotations a ON a.case_id=i.case_id ORDER BY i.reviewer_username, i.queue_rank"""
    ).fetchall()
    affected = [r for r in items if old_words(json.loads(r["payload_json"])["original"]) != page_words(json.loads(r["payload_json"])["original"])]
    print(f"items: {len(items)}  with a decomposed accent: {len(affected)}  touched by a reviewer: {sum(r['state'] is not None for r in affected)}\n")
    for r in affected:
        original = json.loads(r["payload_json"])["original"]
        old = old_words(original)
        first_bad = next(i for i, (a, b) in enumerate(zip(old + [None] * 99, page_words(original))) if a != b)
        later_done = db.execute(
            """SELECT count(*) FROM items i JOIN annotations a ON a.case_id=i.case_id
               WHERE i.reviewer_username=? AND i.queue_rank>? AND a.state='submitted'""",
            (r["reviewer_username"], r["queue_rank"]),
        ).fetchone()[0]
        head = f"{r['case_id']}  reviewer={r['reviewer_username']}  queue={r['queue_rank']}  state={r['state'] or 'not opened'}"
        if r["state"] is None:
            print(f"{head}\n    not reached yet: will work after the fix\n")
            continue
        answer = json.loads(r["answer_json"] or "{}")
        history = db.execute(
            "SELECT new_answer_json, new_state, changed_at FROM revisions WHERE case_id=? ORDER BY revision_id", (r["case_id"],)
        ).fetchall()
        ever_rejected = sorted({w for h in history for w in rejected(json.loads(h["new_answer_json"]), old)})
        if r["state"] == "draft":
            now = rejected(answer, old)
            verdict = ("BLOCKED: the draft selects " + ", ".join(now) + " and could not be submitted") if now else "draft, no blocked word selected yet"
        elif answer.get("skipped"):
            verdict = "SKIPPED" + (f" after selecting {', '.join(ever_rejected)} (likely because of the bug)" if ever_rejected else "")
        elif ever_rejected:
            verdict = f"SUBMITTED AFTER DROPPING {', '.join(ever_rejected)} from the selection (workaround; the selection is incomplete)"
        else:
            verdict = "submitted normally (only words before the accent selected)"
        print(f"{head}\n    first word that differs: #{first_bad} {page_words(original)[first_bad][2]!r}\n    {verdict}")
        print(f"    later items submitted by this reviewer: {later_done}   last change: {r['updated_at']}\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/data/s1_validation_v1.sqlite3")
