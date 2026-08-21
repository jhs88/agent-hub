"""Build the transport-neutral, aggregate-only Agent Hub snapshot."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from .config import SUPPORTED_AGENTS, get_default_agent

SCHEMA_VERSION = 1
TOKEN_FIELDS = (
    "inputTokens",
    "outputTokens",
    "cacheReadInputTokens",
    "cacheCreationInputTokens",
)
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _xdg_path(variable: str, fallback: str) -> Path:
    value = os.environ.get(variable)
    return Path(value) if value else Path.home() / fallback


def usage_dir() -> Path:
    return _xdg_path("XDG_STATE_HOME", ".local/state") / "agent-hub/usage"



def _number(value: Any) -> int:
    try:
        return max(0, round(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def _text(value: Any, limit: int = 240) -> str:
    text = "".join(character for character in str(value or "") if character >= " " and character != "\x7f")
    return text[:limit]


def _model_usage(value: Any) -> dict[str, dict[str, int]]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, dict[str, int]] = {}
    for raw_name, raw_bucket in value.items():
        name = _text(raw_name, 120)
        if not name or not isinstance(raw_bucket, dict):
            continue
        result[name] = {field: _number(raw_bucket.get(field)) for field in TOKEN_FIELDS}
    return result


def _tokens_by_model(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {_text(name, 120): _number(total) for name, total in value.items() if _text(name, 120)}


def _limits(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        try:
            percent = min(1.0, max(0.0, float(raw.get("percent") or 0)))
        except (TypeError, ValueError):
            percent = 0.0
        result.append({
            "label": _text(raw.get("label"), 120),
            "percent": percent,
            "resetsAt": _text(raw.get("resetsAt"), 80),
        })
    return result


def _recent_days(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result = []
    for raw in value:
        if isinstance(raw, dict):
            result.append({
                "date": _text(raw.get("date"), 20),
                "messageCount": _number(raw.get("messageCount")),
            })
    return result


def sanitize_provider(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    provider_id = _text(raw.get("id"), 64).lower()
    if not _ID.fullmatch(provider_id):
        return None
    active_value = raw.get("activeDates")
    active_dates = active_value if isinstance(active_value, list) else []
    return {
        "schemaVersion": _number(raw.get("schemaVersion")) or 1,
        "id": provider_id,
        "name": _text(raw.get("name") or provider_id, 120),
        "updatedAt": _text(raw.get("updatedAt"), 80),
        "ready": bool(raw.get("ready")),
        "hasLocalStats": bool(raw.get("hasLocalStats")),
        "hasPromptStats": bool(raw.get("hasPromptStats")),
        "tierLabel": _text(raw.get("tierLabel"), 120),
        "usageStatusText": _text(raw.get("usageStatusText")),
        "authHelpText": _text(raw.get("authHelpText")),
        "limits": _limits(raw.get("limits")),
        "todayPrompts": _number(raw.get("todayPrompts")),
        "todaySessions": _number(raw.get("todaySessions")),
        "todayTotalTokens": _number(raw.get("todayTotalTokens")),
        "todayTokensByModel": _tokens_by_model(raw.get("todayTokensByModel")),
        "recentDays": _recent_days(raw.get("recentDays")),
        "modelUsage": _model_usage(raw.get("modelUsage")),
        "totalPrompts": _number(raw.get("totalPrompts")),
        "totalSessions": _number(raw.get("totalSessions")),
        "activeDays": _number(raw.get("activeDays")),
        "activeDates": [_text(day, 20) for day in active_dates if _text(day, 20)],
    }


def load_providers(directory: Path | None = None) -> list[dict[str, Any]]:
    root = directory or usage_dir()
    providers = []
    if root.is_dir():
        for path in root.glob("*.json"):
            try:
                if path.stat().st_size > 1_048_576:
                    continue
                provider = sanitize_provider(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError):
                continue
            if provider is not None:
                providers.append(provider)
    order = {"codex": 0, "local": 1}
    providers.sort(key=lambda row: (order.get(row["id"], 99), row["id"]))
    return providers


def build_snapshot() -> dict[str, Any]:
    providers = load_providers()
    refreshed_at = max((row["updatedAt"] for row in providers), default="")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "refreshedAt": refreshed_at,
        "providers": providers,
        "agents": [{"id": agent, "installed": bool(shutil.which(agent))} for agent in SUPPORTED_AGENTS],
        "defaultAgent": get_default_agent(),
        "privacy": {"contentRetained": False},
    }
