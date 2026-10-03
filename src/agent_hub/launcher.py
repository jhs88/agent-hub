"""Desktop-neutral coding-agent launch adapter."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from .config import SUPPORTED_AGENTS, get_default_agent, installed_agent, working_directory

TERMINALS = ("ghostty", "konsole", "kitty", "alacritty", "foot", "xterm")


def terminal_path() -> str:
    for command in TERMINALS:
        path = shutil.which(command)
        if path:
            return path
    raise FileNotFoundError("no supported terminal is installed")


def launch_spec(agent: str | None = None) -> dict[str, Any]:
    selected = agent or get_default_agent()
    if not selected:
        choices = "|".join(SUPPORTED_AGENTS)
        raise ValueError(f"no default agent selected; run: agent-hub default set <{choices}>")
    agent_path = installed_agent(selected)
    systemd_run = shutil.which("systemd-run")
    if not systemd_run:
        raise FileNotFoundError("systemd-run is not installed")
    terminal = terminal_path()
    cwd = working_directory()
    properties = ["--property=Type=exec"]
    if selected == "hermes":
        # A new interactive session must not inherit an automation source label.
        properties.append("--property=UnsetEnvironment=HERMES_SESSION_SOURCE")
    return {
        "agent": selected,
        "cwd": str(cwd),
        "argv": [
            systemd_run,
            "--user",
            "--collect",
            "--quiet",
            *properties,
            f"--working-directory={cwd}",
            terminal,
            "-e",
            agent_path,
        ],
    }


def launch(agent: str | None = None) -> dict[str, Any]:
    spec = launch_spec(agent)
    subprocess.run(spec["argv"], check=True)
    return spec
