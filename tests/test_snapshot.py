#!/usr/bin/env python3
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_hub.snapshot import build_snapshot


class SnapshotContractTest(unittest.TestCase):
    def test_snapshot_is_allowlisted_aggregate_only_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            state = home / "state"
            config = home / "config"
            usage = state / "agent-hub/usage"
            binaries = home / "bin"
            usage.mkdir(parents=True)
            (config / "agent-hub").mkdir(parents=True)
            binaries.mkdir()

            for name in ("pi", "codex"):
                executable = binaries / name
                executable.write_text("#!/bin/sh\nexit 0\n")
                executable.chmod(0o755)

            (config / "agent-hub/default-agent").write_text("pi\n")
            (usage / "codex.json").write_text(json.dumps({
                "schemaVersion": 1,
                "id": "codex",
                "name": "Codex",
                "updatedAt": "2026-08-21T18:00:00+00:00",
                "ready": True,
                "hasLocalStats": True,
                "hasPromptStats": True,
                "tierLabel": "prolite",
                "usageStatusText": "",
                "authHelpText": "",
                "limits": [{"label": "Weekly", "percent": 0.2, "resetsAt": "2026-08-28T00:00:00+00:00", "token": "PRIVATE_LIMIT_TOKEN"}],
                "todayPrompts": 2,
                "todaySessions": 1,
                "todayTotalTokens": 42,
                "todayTokensByModel": {"gpt-5.6-sol": 42},
                "recentDays": [{"date": "2026-08-21", "messageCount": 42, "content": "PRIVATE_DAY_PROMPT"}],
                "modelUsage": {"gpt-5.6-sol": {"inputTokens": 30, "outputTokens": 12, "content": "PRIVATE_MODEL_RESPONSE"}},
                "totalPrompts": 9,
                "totalSessions": 3,
                "activeDays": 2,
                "activeDates": ["2026-08-20", "2026-08-21"],
                "content": "PRIVATE_PROVIDER_PROMPT",
                "accessToken": "PRIVATE_ACCESS_TOKEN",
            }))
            (usage / "local.json").write_text(json.dumps({
                "schemaVersion": 1,
                "id": "local",
                "name": "Local Models",
                "updatedAt": "2026-08-21T17:00:00+00:00",
                "ready": True,
                "limits": [],
                "todayPrompts": 1,
                "todaySessions": 1,
                "todayTotalTokens": 7,
                "todayTokensByModel": {"qwen": 7},
                "recentDays": [],
                "modelUsage": {"qwen": {"inputTokens": 4, "outputTokens": 3}},
                "totalPrompts": 1,
                "totalSessions": 1,
                "activeDays": 1,
                "activeDates": ["2026-08-21"],
            }))

            env = {
                "HOME": str(home),
                "XDG_STATE_HOME": str(state),
                "XDG_CONFIG_HOME": str(config),
                "PATH": str(binaries),
            }
            with patch.dict(os.environ, env, clear=True):
                snapshot = build_snapshot()

            self.assertEqual(snapshot["schemaVersion"], 1)
            self.assertEqual(snapshot["refreshedAt"], "2026-08-21T18:00:00+00:00")
            self.assertEqual([row["id"] for row in snapshot["providers"]], ["codex", "local"])
            self.assertEqual(snapshot["defaultAgent"], "pi")
            self.assertEqual(snapshot["agents"], [
                {"id": "pi", "installed": True},
                {"id": "opencode", "installed": False},
                {"id": "codex", "installed": True},
                {"id": "hermes", "installed": False},
            ])
            self.assertEqual(snapshot["privacy"], {"contentRetained": False})

            rendered = json.dumps(snapshot)
            for forbidden in (
                "PRIVATE_LIMIT_TOKEN",
                "PRIVATE_DAY_PROMPT",
                "PRIVATE_MODEL_RESPONSE",
                "PRIVATE_PROVIDER_PROMPT",
                "PRIVATE_ACCESS_TOKEN",
                "accessToken",
                '"content"',
            ):
                self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":
    unittest.main()
