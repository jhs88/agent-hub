"""Bounded refresh adapter for the migration collector command."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .snapshot import build_snapshot


def collector_path() -> str:
    configured = os.environ.get("AGENT_HUB_COLLECTOR", "").strip()
    if configured:
        path = Path(configured).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"collector not found: {path}")
        return str(path)
    user_local = Path.home() / ".local/bin/agent-hub-collect"
    if user_local.is_file():
        return str(user_local)
    discovered = shutil.which("agent-hub-collect")
    if not discovered:
        raise FileNotFoundError("agent-hub-collect is not installed")
    return discovered


def refresh_snapshot(timeout: int = 30) -> dict[str, Any]:
    command = collector_path()
    subprocess.run(
        [command],
        check=True,
        timeout=timeout,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return build_snapshot()
