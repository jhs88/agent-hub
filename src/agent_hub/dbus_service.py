"""Session D-Bus contract and dependency-injected method implementation."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from .config import set_default_agent
from .launcher import launch
from .refresh import refresh_snapshot
from .snapshot import build_snapshot

BUS_NAME = "io.github.jhs88.AgentHub"
INTERFACE_NAME = "io.github.jhs88.AgentHub1"
OBJECT_PATH = "/io/github/jhs88/AgentHub"

INTROSPECTION_XML = f"""
<node>
  <interface name="{INTERFACE_NAME}">
    <method name="GetSnapshot">
      <arg type="s" name="snapshotJSON" direction="out"/>
    </method>
    <method name="Refresh">
      <arg type="s" name="snapshotJSON" direction="out"/>
    </method>
    <method name="SetDefaultAgent">
      <arg type="s" name="agent" direction="in"/>
      <arg type="s" name="snapshotJSON" direction="out"/>
    </method>
    <method name="Launch">
      <arg type="s" name="agent" direction="in"/>
      <arg type="s" name="snapshotJSON" direction="out"/>
    </method>
    <signal name="Changed">
      <arg type="s" name="snapshotJSON"/>
    </signal>
  </interface>
</node>
""".strip()


class AgentHubMethods:
    """Deep method module shared by D-Bus and direct tests."""

    def __init__(
        self,
        *,
        snapshot_builder: Callable[[], dict[str, Any]] = build_snapshot,
        refresher: Callable[[], dict[str, Any]] = refresh_snapshot,
        default_setter: Callable[[str], str] = set_default_agent,
        launcher: Callable[[str | None], dict[str, Any]] = launch,
    ):
        self._snapshot_builder = snapshot_builder
        self._refresher = refresher
        self._default_setter = default_setter
        self._launcher = launcher

    @staticmethod
    def _encode(snapshot: dict[str, Any]) -> str:
        return json.dumps(snapshot, separators=(",", ":"), sort_keys=True)

    def get_snapshot(self) -> str:
        return self._encode(self._snapshot_builder())

    def refresh(self) -> str:
        return self._encode(self._refresher())

    def set_default_agent(self, agent: str) -> str:
        self._default_setter(agent)
        return self.get_snapshot()

    def launch_agent(self, agent: str) -> str:
        self._launcher(agent or None)
        return self.get_snapshot()


def serve() -> None:
    """Own the session-bus name and serve until the graphical session ends."""
    try:
        import gi  # type: ignore[import-not-found]

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("Agent Hub D-Bus service requires PyGObject/Gio") from exc

    methods = AgentHubMethods()
    node = Gio.DBusNodeInfo.new_for_xml(INTROSPECTION_XML)
    interface = node.interfaces[0]
    loop = GLib.MainLoop()
    registration_id = 0

    def changed(connection, payload: str) -> None:
        connection.emit_signal(
            None,
            OBJECT_PATH,
            INTERFACE_NAME,
            "Changed",
            GLib.Variant("(s)", (payload,)),
        )

    def method_call(connection, _sender, _path, _interface, method_name, parameters, invocation):
        try:
            arguments = parameters.unpack()
            should_emit = False
            if method_name == "GetSnapshot":
                payload = methods.get_snapshot()
            elif method_name == "Refresh":
                payload = methods.refresh()
                should_emit = True
            elif method_name == "SetDefaultAgent":
                payload = methods.set_default_agent(arguments[0])
                should_emit = True
            elif method_name == "Launch":
                payload = methods.launch_agent(arguments[0])
            else:
                raise ValueError(f"unknown method: {method_name}")
            invocation.return_value(GLib.Variant("(s)", (payload,)))
            if should_emit:
                changed(connection, payload)
        except Exception as exc:
            detail = str(exc).replace("\n", " ")[:240]
            invocation.return_dbus_error(f"{INTERFACE_NAME}.Error", detail)

    def bus_acquired(connection, _name):
        nonlocal registration_id
        registration_id = connection.register_object(OBJECT_PATH, interface, method_call, None, None)

    def name_lost(_connection, _name):
        loop.quit()

    owner_id = Gio.bus_own_name(
        Gio.BusType.SESSION,
        BUS_NAME,
        Gio.BusNameOwnerFlags.NONE,
        bus_acquired,
        None,
        name_lost,
    )
    try:
        loop.run()
    finally:
        Gio.bus_unown_name(owner_id)
        del registration_id
