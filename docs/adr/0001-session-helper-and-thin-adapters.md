# ADR-0001: Session helper with thin desktop adapters

- Status: Accepted
- Date: 2026-08-21

## Context

Agent Hub must work in Plasma and Noctalia without duplicating private history parsing, credentials, refresh policy, or launch behavior inside each shell. Plasma's executable DataSource works today but is a compatibility engine and places command execution in `plasmashell`.

## Decision

Use one user-session helper with a transport-neutral JSON Snapshot and stable session D-Bus interface. Plasma is a QML-only D-Bus client. Other desktops use equally thin clients over the same helper or CLI compatibility surface.

The helper owns private reads, refresh, sanitization, default-agent configuration, and launch policy. Desktop adapters own presentation and per-instance UI state only.

## Consequences

- Shell adapters cannot expose provider credentials or histories accidentally.
- One refresh and launch implementation serves every desktop.
- Installation has two artifacts: helper/runtime files and desktop adapter packages.
- D-Bus/Gio is an additional runtime dependency for the session service.
- Legacy CLI aliases remain until existing Noctalia callers migrate.
