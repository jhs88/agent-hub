"""Agent Hub command-line client."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

from .config import SUPPORTED_AGENTS, get_default_agent, set_default_agent
from .launcher import launch, launch_spec
from .refresh import refresh_snapshot
from .snapshot import build_snapshot


def _json(payload) -> None:
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="agent-hub")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot")
    commands.add_parser("refresh")
    commands.add_parser("serve")
    commands.add_parser("get", help=argparse.SUPPRESS)
    legacy_set = commands.add_parser("set", help=argparse.SUPPRESS)
    legacy_set.add_argument("agent")

    default = commands.add_parser("default")
    default_commands = default.add_subparsers(dest="default_command", required=True)
    default_commands.add_parser("get")
    default_set = default_commands.add_parser("set")
    default_set.add_argument("agent")

    agents = commands.add_parser("agents")
    agents.add_argument("--json", action="store_true")

    launch_command = commands.add_parser("launch")
    launch_command.add_argument("agent", nargs="?")
    launch_command.add_argument("--dry-run", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            _json(build_snapshot())
            return 0
        if args.command == "refresh":
            _json(refresh_snapshot())
            return 0
        if args.command == "serve":
            from .dbus_service import serve

            serve()
            return 0
        if args.command == "get":
            value = get_default_agent()
            if value:
                print(value)
            return 0
        if args.command == "set":
            print(set_default_agent(args.agent))
            return 0
        if args.command == "default":
            if args.default_command == "get":
                value = get_default_agent()
                if value:
                    print(value)
                return 0
            print(set_default_agent(args.agent))
            return 0
        if args.command == "agents":
            rows = [{"id": agent, "installed": bool(shutil.which(agent))} for agent in SUPPORTED_AGENTS]
            if args.json:
                _json(rows)
            else:
                for row in rows:
                    print(f"{row['id']}\t{'installed' if row['installed'] else 'missing'}")
            return 0
        if args.command == "launch":
            spec = launch_spec(args.agent) if args.dry_run else launch(args.agent)
            _json(spec)
            return 0
    except (ValueError, FileNotFoundError, subprocess.SubprocessError) as exc:
        print(f"agent-hub: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
