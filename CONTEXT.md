# Agent Hub domain context

## Purpose

Agent Hub presents one private, aggregate view of coding-agent activity and quota across desktop shells, plus one safe policy for choosing and launching an interactive agent.

## Glossary

**Agent** — an installed interactive coding CLI such as Pi, OpenCode, or Codex. An Agent is executable capability, not a model or provider.

**Provider** — the source that reports quota or token activity. A Provider can be remote, local, or a compatibility adapter.

**Provider record** — one collector-owned aggregate record before cross-provider projection.

**Snapshot** — the allow-listed, transport-neutral JSON document returned to every client. It contains Provider aggregates, Agent availability, and Default Agent state. It never contains prompt/response content, credentials, account email, auth headers, or transcript paths.

**Session helper** — the user-session process that owns private file access, refresh, sanitization, configuration, and launch policy. Its stable public seam is `io.github.jhs88.AgentHub1`.

**Desktop adapter** — a presentation client such as the Plasma KPackage or Noctalia plugin. It renders a Snapshot and invokes fixed helper methods; it does not collect data.

**Collector adapter** — a bounded implementation that converts one upstream source into aggregate Provider records.

**Launch adapter** — the desktop-neutral implementation that starts an Agent in a terminal through a transient systemd user unit.

**Default Agent** — the configured Agent selected when a launch request omits an explicit ID.

## Stable interface

```text
GetSnapshot() -> JSON
Refresh() -> JSON
SetDefaultAgent(id) -> JSON
Launch(id) -> JSON
Changed(JSON)
```

## Invariants

- Snapshot fields are recursively allow-listed.
- Desktop adapters never receive or discover credentials and histories.
- Missing data is unknown or absent, never fabricated zero usage.
- Launches remain interactive and contain no implicit permission bypass.
- D-Bus and CLI clients share the same method implementation.
- Provider-specific logic remains behind Collector adapters.

## Current migration boundary

The standalone project owns Snapshot, configuration, launch, CLI, D-Bus, installation, and Plasma presentation. Refresh currently invokes the externally installed `agent-hub-collect` command through a shell-free timeout. Moving collectors here and making Noctalia a pure D-Bus client require separate decisions.
