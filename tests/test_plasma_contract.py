#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plasma/package"


class PlasmaContractTest(unittest.TestCase):
    def test_plasma6_widget_is_a_thin_dbus_adapter(self):
        metadata = json.loads((PACKAGE / "metadata.json").read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], "io.github.jhs88.agenthub")
        self.assertEqual(metadata["X-Plasma-API-Minimum-Version"], "6.0")
        self.assertEqual(metadata["KPackageStructure"], "Plasma/Applet")

        qml = (PACKAGE / "contents/ui/main.qml").read_text()
        self.assertIn("PlasmoidItem", qml)
        self.assertIn("org.kde.plasma.workspace.dbus as DBus", qml)
        self.assertIn('watchedService: "io.github.jhs88.AgentHub"', qml)
        self.assertIn('call("GetSnapshot"', qml)
        self.assertIn('call("Refresh"', qml)
        self.assertIn('call("SetDefaultAgent"', qml)
        self.assertIn('call("Launch"', qml)
        self.assertIn("compactRepresentation", qml)
        self.assertIn("fullRepresentation", qml)

        for forbidden in (
            "Plasma5Support",
            "DataSource",
            'engine: "executable"',
            ".credentials",
            "auth.json",
            ".codex/sessions",
            "session.jsonl",
            "opencode.db",
            "accessToken",
        ):
            self.assertNotIn(forbidden, qml)


if __name__ == "__main__":
    unittest.main()
