#!/usr/bin/env python3
import json
import unittest

from agent_hub.dbus_service import AgentHubMethods


class DbusMethodsTest(unittest.TestCase):
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
