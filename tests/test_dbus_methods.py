#!/usr/bin/env python3
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_hub.dbus_service import AgentHubMethods


class DbusMethodsTest(unittest.TestCase):
    def test_hermes_uses_shared_default_snapshot_and_launch_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            binaries = home / "bin"
            binaries.mkdir()
            for name in ("hermes", "ghostty", "systemd-run"):
                executable = binaries / name
                executable.write_text("#!/bin/sh\nexit 0\n")
                executable.chmod(0o755)
            env = {
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / "config"),
                "XDG_STATE_HOME": str(home / "state"),
                "PATH": str(binaries),
                "HERMES_SESSION_SOURCE": "tool",
            }
            with patch.dict(os.environ, env, clear=True):
                methods = AgentHubMethods()
                selected = json.loads(methods.set_default_agent("hermes"))
                self.assertEqual(selected["defaultAgent"], "hermes")
                self.assertEqual(selected["agents"][-1], {"id": "hermes", "installed": True})
                self.assertEqual(selected["providers"], [])
                self.assertEqual(json.loads(methods.get_snapshot()), selected)
                with patch("agent_hub.launcher.subprocess.run") as run:
                    for agent in ("hermes", ""):
                        with self.subTest(agent=agent):
                            self.assertEqual(json.loads(methods.launch_agent(agent)), selected)
                            run.assert_called_with([
                                str(binaries / "systemd-run"),
                                "--user", "--collect", "--quiet", "--property=Type=exec",
                                "--property=UnsetEnvironment=HERMES_SESSION_SOURCE",
                                f"--working-directory={home}",
                                str(binaries / "ghostty"), "-e", str(binaries / "hermes"),
                            ], check=True)

    def test_methods_delegate_and_return_snapshot_json(self):
        calls = []
        state = {"schemaVersion": 1, "defaultAgent": "pi", "providers": []}

        def snapshot():
            return dict(state)

        def refresh():
            calls.append(("refresh",))
            state["providers"] = [{"id": "codex"}]
            return snapshot()

        def set_default(agent):
            calls.append(("default", agent))
            state["defaultAgent"] = agent
            return agent

        def launch(agent=None):
            calls.append(("launch", agent))
            return {"agent": agent or state["defaultAgent"]}

        methods = AgentHubMethods(
            snapshot_builder=snapshot,
            refresher=refresh,
            default_setter=set_default,
            launcher=launch,
        )

        self.assertEqual(json.loads(methods.get_snapshot()), state)
        self.assertEqual(json.loads(methods.refresh()), state)
        self.assertEqual(json.loads(methods.set_default_agent("codex")), state)
        self.assertEqual(json.loads(methods.launch_agent("")), state)
        self.assertEqual(calls, [
            ("refresh",),
            ("default", "codex"),
            ("launch", None),
        ])


if __name__ == "__main__":
    unittest.main()
