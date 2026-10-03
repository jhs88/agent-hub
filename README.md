# Agent Hub

A desktop-neutral coding-agent activity, quota, and launcher service with thin desktop adapters.

## First vertical slice

- aggregate-only snapshot core;
- session D-Bus helper using Python and Gio;
- command-line snapshot/debug client;
- Plasma 6 smoke widget that reads only D-Bus;
- compatibility with the existing Noctalia Agent Hub records.

The current Noctalia plugin and dotfiles deployment remain separate until this interface is proven.

## Privacy contract

Agent Hub may read local coding-agent histories and provider status through bounded adapters. Its public snapshot contains only provider/model/timestamp/token totals, limit windows, agent availability, and the selected default agent. It never emits or persists prompt text, response text, credentials, auth headers, account email, or transcript paths.

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -v tests
```

Plasma 6 live testing uses `qmllint`, `kpackagetool6`, and `plasmawindowed` on a Plasma 6 development host.

The core and CLI use the Python standard library. The session D-Bus helper additionally requires PyGObject with Gio (`python-gobject` on Arch Linux).

## Install for the current user

```bash
./install-user.sh
```

This creates a dated backup, installs the core under `$XDG_DATA_HOME/agent-hub`, preserves the legacy `agent-hub get/set/launch` interface used by the existing Noctalia plugin, enables the session helper for future logins, and installs the Plasma widget. It does not add the widget to a panel automatically.

After logging into KDE Plasma, open **Add Widgets**, search for **Agent Hub**, and place it in the panel. Use `--no-activate` or `--no-plasma` when staging only part of the installation.

## Run the first slice

Read the current aggregate snapshot directly:

```bash
PYTHONPATH=src python3 -m agent_hub.cli snapshot
```

Start the session helper against the migration collector:

```bash
AGENT_HUB_COLLECTOR="$HOME/.local/bin/agent-hub-collect" \
  PYTHONPATH=src python3 -m agent_hub.cli serve
```

Read it over D-Bus:

```bash
gdbus call --session \
  --dest io.github.jhs88.AgentHub \
  --object-path /io/github/jhs88/AgentHub \
  --method io.github.jhs88.AgentHub1.GetSnapshot
```

The activation templates are in `contrib/systemd/` and `contrib/dbus/`. The Plasma KPackage is under `plasma/package/`; see [`plasma/README.md`](plasma/README.md).

## Interactive agents

Agent Hub supports installed `pi`, `opencode`, `codex`, and `hermes` executables on `PATH`. The CLI and snapshot report availability. Plasma builds its default-agent picker from that snapshot and disables missing agents. Adding Hermes support does not change an existing default.

```bash
agent-hub agents --json
agent-hub launch hermes --dry-run
agent-hub launch hermes
```

An explicit launch leaves the selected default unchanged. To choose Hermes as the default yourself, run `agent-hub default set hermes`. Selection fails if the executable is missing.

Launches use the configured Agent Hub working directory, a supported terminal, and a transient systemd user unit. Hermes starts with its bare executable, which opens interactive chat according to the [Hermes CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands). Agent Hub adds no `--yolo`, approval bypass, query, model, provider, or profile flags. It does not install Hermes or modify its configuration or approval settings.

For Hermes launches only, the transient unit sets `UnsetEnvironment=HERMES_SESSION_SOURCE`. Hermes otherwise uses an inherited source label for its new session, which could incorrectly label a human launch as automation. Other agents' launch commands and environments remain unchanged. Hermes activity and quota collection are not added by launcher support.

## Current migration boundary

`GetSnapshot`, default-agent configuration, safe launching, D-Bus, and the Plasma client are owned here. `Refresh` currently invokes the existing `agent-hub-collect` executable through an absolute, shell-free, 30-second bounded adapter. Provider collectors will move behind native adapters in the next slice. An optional `ai-usagebar usage --json` quota adapter can then replace duplicated provider-specific quota code without making `ai-usagebar` mandatory.

Contributor and agent workflow context lives in [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), and [`docs/adr/`](docs/adr/).
