# Plasma 6 adapter

A QML-only KPackage for Plasma 6. It reads aggregate state and invokes fixed actions through `io.github.jhs88.AgentHub1` on the session bus. It does not use Plasma5Support's executable engine and does not read histories or credentials.

## Validate

```bash
qmllint package/contents/ui/main.qml
python3 -m json.tool package/metadata.json
kpackagetool6 --appstream-metainfo "$PWD/package"
```

## Disposable smoke test

With `agent-hub serve` running:

```bash
kpackagetool6 --type Plasma/Applet --install package
plasmawindowed io.github.jhs88.agenthub
kpackagetool6 --type Plasma/Applet --remove io.github.jhs88.agenthub
```

This first slice renders provider selection, subscription limits, today's aggregate tokens/prompts/sessions, refresh and launch actions, and default-agent selection. It intentionally leaves detailed seven-day/model charts for the next visual slice.

The default-agent picker uses `snapshot.agents`, including Pi, OpenCode, Codex, and Hermes. Missing executables are disabled. The helper owns selection and interactive launch policy; the widget does not install agents or change their configuration.

For a persistent user installation of the core, session helper, and widget together, run `../install-user.sh` from the repository root.
