from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reaction_yield_ml.config import REPORTS_DIR, ensure_directories
from reaction_yield_ml.reporting.io import read_json, write_json

STATE_PATH = REPORTS_DIR / "run_state.json"
LOG_PATH = REPORTS_DIR / "run_log.md"


def update_run_state(
    stage: str,
    status: str,
    files: list[str] | None = None,
    checks: list[str] | None = None,
    failures: list[str] | None = None,
    repairs: list[str] | None = None,
    limitations: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    ensure_directories()
    now = datetime.now(timezone.utc).isoformat()
    state = read_json(STATE_PATH, default={"stages": {}, "updated_at": None})
    entry = {
        "stage": stage,
        "status": status,
        "updated_at": now,
        "files_created_or_updated": files or [],
        "checks_run": checks or [],
        "failures_found": failures or [],
        "repairs_attempted": repairs or [],
        "remaining_limitations": limitations or [],
    }
    if extra:
        entry["extra"] = extra
    state.setdefault("stages", {})[stage] = entry
    state["updated_at"] = now
    write_json(STATE_PATH, state)
    _append_log(stage, entry)


def _append_log(stage: str, entry: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("# Project Run Log\n\n", encoding="utf-8")
    lines = [
        f"## {entry['updated_at']} - {stage}",
        "",
        f"- status: {entry['status']}",
        f"- files created/updated: {', '.join(entry['files_created_or_updated']) or 'none'}",
        f"- checks run: {', '.join(entry['checks_run']) or 'none'}",
        f"- failures found: {', '.join(entry['failures_found']) or 'none'}",
        f"- repairs attempted: {', '.join(entry['repairs_attempted']) or 'none'}",
        f"- remaining limitations: {', '.join(entry['remaining_limitations']) or 'none'}",
        "",
    ]
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
