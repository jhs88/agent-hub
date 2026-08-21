# Agent instructions

## Project

Agent Hub is a cross-desktop coding-agent activity, quota, and safe-launch service. Read `CONTEXT.md` before changing domain language or module ownership, and read relevant records under `docs/adr/` before changing an established seam.

## Working rules

- Keep the session helper deep: histories, credentials, refresh, sanitization, and launch policy stay behind the D-Bus/JSON interface.
- Keep Plasma and Noctalia adapters thin. They render snapshots and invoke fixed actions; they do not parse histories or read credentials.
- Preserve the allow-listed aggregate-only privacy contract. Unknown upstream fields must not pass through automatically.
- Keep launches interactive and desktop-neutral. Approval-bypass flags require a separate explicit policy decision.
- Treat `agent-hub-collect` as a transitional external adapter until a ticket deliberately moves collectors here.
- Use red-before-green vertical slices at the confirmed public seams.
- Run `PYTHONPATH=src python3 -m unittest discover -v tests`, Python compilation, shell syntax checks, metadata validation, and `git diff --check` before handoff.
- Do not commit, push, create a PR, merge, publish, or release unless the user explicitly authorizes that stage.

## Source map

- `src/agent_hub/`: snapshot, configuration, refresh, launch, CLI, and D-Bus modules.
- `plasma/`: QML-only Plasma 6 adapter.
- `contrib/`: user-service, D-Bus activation, and launcher files.
- `tests/`: public-interface contract tests.
- `DESIGN.md`: current architecture and migration boundary.

## Agent skills

### Issue tracker

Hermes Kanban board `agent-hub` is the primary work tracker; GitHub Issues are used only when explicitly requested. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical Matt triage roles map to Hermes Kanban states rather than mirror labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. Read `CONTEXT.md` and relevant decisions under `docs/adr/`. See `docs/agents/domain.md`.
