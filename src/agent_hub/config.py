"""User-owned Agent Hub configuration."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

SUPPORTED_AGENTS = ("pi", "opencode", "codex")


def config_dir() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return root / "agent-hub"


def default_agent_file() -> Path:
    return config_dir() / "default-agent"


def working_directory_file() -> Path:
    return config_dir() / "working-directory"


def installed_agent(agent: str) -> str:
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(f"unsupported agent: {agent}")
    executable = shutil.which(agent)
    if not executable:
        raise FileNotFoundError(f"{agent} is not installed")
    return executable


def get_default_agent() -> str:
    try:
        value = default_agent_file().read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return value if value in SUPPORTED_AGENTS else ""


def set_default_agent(agent: str) -> str:
    installed_agent(agent)
    path = default_agent_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(agent + "\n", encoding="utf-8")
    temp.chmod(0o600)
    os.replace(temp, path)
    return agent


def working_directory() -> Path:
    try:
        raw = working_directory_file().read_text(encoding="utf-8").strip()
    except OSError:
        raw = ""
    candidate = Path(os.path.expandvars(os.path.expanduser(raw))) if raw else Path.home()
    return candidate if candidate.is_dir() else Path.home()
