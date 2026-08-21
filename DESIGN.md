# Design

## Deep module

The external seam is one transport-neutral snapshot plus four commands:

- `GetSnapshot() -> JSON`
- `Refresh() -> JSON`
- `SetDefaultAgent(id) -> JSON`
- `Launch(id) -> JSON`
- `Changed(JSON)` signal

Collectors, credential ownership, history formats, cache policy, terminal selection, and process launching stay behind this interface.

## Adapters

- **Activity:** Pi, OpenCode, Codex, and local-model aggregates.
- **Quota:** optional `ai-usagebar usage --json`; direct Codex app-server fallback during migration.
- **Launcher:** desktop-neutral transient systemd user unit and a configured terminal.
- **Plasma:** QML-only Plasma 6 KPackage using session D-Bus.
- **Noctalia:** thin client after the seam is proven.

## Ownership

`agent-hubd` owns local history access, refresh, sanitization, aggregate state, and launch policy. Desktop adapters own presentation and per-instance UI selection only. They never read credentials or histories and never execute provider commands.

## Migration boundary

The first slice consumes the existing aggregate record directory and invokes the current collector as an injected external command for refresh. Moving collectors into this repository is the next slice, not an implicit fallback.
