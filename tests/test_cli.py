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

    def test_missing_hermes_is_reported_without_changing_default(self):
        self.run_cli("default", "set", "pi")
        agents = json.loads(self.run_cli("agents", "--json").stdout)
        self.assertEqual(agents, [
            {"id": "pi", "installed": True},
            {"id": "opencode", "installed": False},
            {"id": "codex", "installed": True},
            {"id": "hermes", "installed": False},
        ])
        self.assertIn("hermes\tmissing", self.run_cli("agents").stdout)
        snapshot = json.loads(self.run_cli("snapshot").stdout)
        self.assertEqual(snapshot["agents"], agents)
        self.assertEqual(snapshot["defaultAgent"], "pi")
        for args in (("default", "set", "hermes"), ("launch", "hermes", "--dry-run")):
            with self.subTest(args=args):
                result = self.run_cli(*args, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn("hermes is not installed", result.stderr)
                self.assertEqual(self.run_cli("default", "get").stdout.strip(), "pi")

    def test_installed_hermes_launches_interactively_and_can_be_selected(self):
        executable = self.bin / "hermes"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        capture = self.home / "launch-argv.json"
        runner = self.bin / "systemd-run"
        runner.write_text(
            f"#!{sys.executable}\n"
            "import json, sys\n"
            "from pathlib import Path\n"
            f"Path({str(capture)!r}).write_text(json.dumps(sys.argv[1:]))\n"
        )
        self.env["HERMES_SESSION_SOURCE"] = "tool"
        workspace = self.home / "project with spaces"
        workspace.mkdir()
        (self.config / "agent-hub/working-directory").write_text(str(workspace) + "\n")
        self.run_cli("default", "set", "pi")
        expected_argv = [
            str(runner),
            "--user",
            "--collect",
            "--quiet",
            "--property=Type=exec",
            "--property=UnsetEnvironment=HERMES_SESSION_SOURCE",
            f"--working-directory={workspace}",
            str(self.bin / "ghostty"),
            "-e",
            str(executable),
        ]
        explicit = json.loads(self.run_cli("launch", "hermes", "--dry-run").stdout)
        self.assertEqual(explicit, {"agent": "hermes", "cwd": str(workspace), "argv": expected_argv})
        self.assertFalse(capture.exists())
        self.assertEqual(self.run_cli("default", "get").stdout.strip(), "pi")
        agents = json.loads(self.run_cli("agents", "--json").stdout)
        self.assertEqual(agents[-1], {"id": "hermes", "installed": True})
        self.assertIn("hermes\tinstalled", self.run_cli("agents").stdout)

        self.assertEqual(self.run_cli("default", "set", "hermes").stdout.strip(), "hermes")
        self.assertEqual(self.run_cli("default", "get").stdout.strip(), "hermes")
        self.assertEqual((self.config / "agent-hub/default-agent").read_text(), "hermes\n")
        snapshot = json.loads(self.run_cli("snapshot").stdout)
        self.assertEqual(snapshot["defaultAgent"], "hermes")
        self.assertEqual(snapshot["agents"], agents)
        self.assertEqual(snapshot["providers"], [])
        self.assertEqual(json.loads(self.run_cli("launch", "--dry-run").stdout), explicit)
        self.assertEqual(json.loads(self.run_cli("launch").stdout), explicit)
        self.assertEqual(json.loads(capture.read_text()), expected_argv[1:])
        self.assertEqual(self.run_cli("get").stdout.strip(), "hermes")
        self.assertEqual(self.run_cli("set", "codex").stdout.strip(), "codex")

    def test_existing_agents_keep_launch_policy_and_selected_default(self):
        executable = self.bin / "opencode"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        self.env["HERMES_SESSION_SOURCE"] = "tool"
        for agent in ("pi", "opencode", "codex"):
            with self.subTest(agent=agent):
                # Simulate a default chosen before Hermes support was added.
                default = self.config / "agent-hub/default-agent"
                default.write_text(agent + "\n")
                self.assertEqual(self.run_cli("default", "get").stdout.strip(), agent)
                self.assertEqual(json.loads(self.run_cli("snapshot").stdout)["defaultAgent"], agent)
                expected = [
                    str(self.bin / "systemd-run"),
                    "--user", "--collect", "--quiet", "--property=Type=exec",
                    f"--working-directory={self.home}",
                    str(self.bin / "ghostty"), "-e", str(self.bin / agent),
                ]
                for args in (("launch", "--dry-run"), ("launch", agent, "--dry-run")):
                    spec = json.loads(self.run_cli(*args).stdout)
                    self.assertEqual(spec["agent"], agent)
                    self.assertEqual(spec["argv"], expected)
                self.assertEqual(self.run_cli("default", "set", agent).stdout.strip(), agent)
                self.assertEqual(default.read_text(), agent + "\n")

    def test_no_default_launch_guidance_includes_hermes_without_selecting_it(self):
        result = self.run_cli("launch", "--dry-run", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("agent-hub default set <pi|opencode|codex|hermes>", result.stderr)
        self.assertFalse((self.config / "agent-hub/default-agent").exists())

    def test_legacy_noctalia_get_and_set_aliases_remain_compatible(self):
        self.assertEqual(self.run_cli("get").stdout, "")
        self.assertEqual(self.run_cli("set", "pi").stdout.strip(), "pi")
        self.assertEqual(self.run_cli("get").stdout.strip(), "pi")


if __name__ == "__main__":
    unittest.main()
