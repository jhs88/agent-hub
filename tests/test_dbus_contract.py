#!/usr/bin/env python3
import unittest
import xml.etree.ElementTree as ET

from agent_hub.dbus_service import BUS_NAME, INTERFACE_NAME, INTROSPECTION_XML, OBJECT_PATH


class DbusContractTest(unittest.TestCase):
    def test_interface_names_methods_and_signal_are_stable(self):
        self.assertEqual(BUS_NAME, "io.github.jhs88.AgentHub")
        self.assertEqual(INTERFACE_NAME, "io.github.jhs88.AgentHub1")
        self.assertEqual(OBJECT_PATH, "/io/github/jhs88/AgentHub")

        # INTROSPECTION_XML is a trusted source constant, never external XML.
        document = ET.fromstring(INTROSPECTION_XML)
        interface = document.find(f"interface[@name='{INTERFACE_NAME}']")
        assert interface is not None
        self.assertEqual(
            [node.attrib["name"] for node in interface.findall("method")],
            ["GetSnapshot", "Refresh", "SetDefaultAgent", "Launch"],
        )
        self.assertEqual(
            [node.attrib["name"] for node in interface.findall("signal")],
            ["Changed"],
        )
        for method in interface.findall("method"):
            outputs = [arg for arg in method.findall("arg") if arg.attrib.get("direction") == "out"]
            self.assertEqual([(arg.attrib["type"], arg.attrib["name"]) for arg in outputs], [("s", "snapshotJSON")])


if __name__ == "__main__":
    unittest.main()
