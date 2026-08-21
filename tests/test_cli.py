#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.state = self.home / "state"
        self.config = self.home / "config"
        self.bin = self.home / "bin"
        (self.state / "agent-hub/usage").mkdir(parents=True)
        (self.config / "agent-hub").mkdir(parents=True)
        self.bin.mkdir()
        for name in ("systemd-run", "ghostty", "pi", "codex"):
            path = self.bin / name
            path.write_text("#!/bin/sh\nexit 0\n")
            path.chmod(0o755)
        self.env = os.environ.copy()
        self.env.update({
            "HOME": str(self.home),
            "XDG_STATE_HOME": str(self.state),
            "XDG_CONFIG_HOME": str(self.config),
            "PATH": str(self.bin),
            "PYTHONPATH": str(ROOT / "src"),
        })

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, check=True):
        result = subprocess.run(
            [sys.executable, "-m", "agent_hub.cli", *args],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_cli_persists_default_and_builds_desktop_neutral_launch(self):
        self.assertEqual(self.run_cli("default", "get").stdout, "")
        self.assertEqual(self.run_cli("default", "set", "pi").stdout.strip(), "pi")
        self.assertEqual(self.run_cli("default", "get").stdout.strip(), "pi")

        snapshot = json.loads(self.run_cli("snapshot").stdout)
        self.assertEqual(snapshot["defaultAgent"], "pi")

        launch = json.loads(self.run_cli("launch", "--dry-run").stdout)
        self.assertEqual(launch["agent"], "pi")
        self.assertEqual(launch["cwd"], str(self.home))
        self.assertEqual(launch["argv"], [
            str(self.bin / "systemd-run"),
            "--user",
            "--collect",
            "--quiet",
            "--property=Type=exec",
            f"--working-directory={self.home}",
            str(self.bin / "ghostty"),
            "-e",
            str(self.bin / "pi"),
        ])
        forbidden = {"uwsm-app", "--auto", "--approve-for-me", "--permission-mode", "--yolo", "--allow-all"}
        self.assertTrue(forbidden.isdisjoint(launch["argv"]))

        unsupported = self.run_cli("default", "set", "grok", check=False)
        self.assertNotEqual(unsupported.returncode, 0)
        self.assertIn("unsupported agent", unsupported.stderr)

    def test_legacy_noctalia_get_and_set_aliases_remain_compatible(self):
        self.assertEqual(self.run_cli("get").stdout, "")
        self.assertEqual(self.run_cli("set", "pi").stdout.strip(), "pi")
        self.assertEqual(self.run_cli("get").stdout.strip(), "pi")


if __name__ == "__main__":
    unittest.main()
