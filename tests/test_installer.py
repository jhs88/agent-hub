#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install-user.sh"


class UserInstallerTest(unittest.TestCase):
    def test_isolated_install_backs_up_launcher_and_installs_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config = home / "config"
            data = home / "data"
            state = home / "state"
            old_launcher = home / ".local/bin/agent-hub"
            old_launcher.parent.mkdir(parents=True)
            old_launcher.write_text("old launcher\n")

            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(config),
                "XDG_DATA_HOME": str(data),
                "XDG_STATE_HOME": str(state),
            })
            result = subprocess.run(
                [str(INSTALLER), "--no-activate", "--no-plasma"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            backups = list((state / "agent-hub/install-backups").glob("*/home/.local/bin/agent-hub"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), "old launcher\n")

            launcher = home / ".local/bin/agent-hub"
            self.assertTrue(os.access(launcher, os.X_OK))
            self.assertTrue((data / "agent-hub/python/agent_hub/snapshot.py").is_file())
            self.assertTrue((config / "systemd/user/agent-hub.service").is_file())
            self.assertTrue((data / "dbus-1/services/io.github.jhs88.AgentHub.service").is_file())

            snapshot = subprocess.run(
                [str(launcher), "snapshot"],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
            self.assertEqual(json.loads(snapshot.stdout)["privacy"], {"contentRetained": False})


if __name__ == "__main__":
    unittest.main()
