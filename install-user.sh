#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
state_home="${XDG_STATE_HOME:-$HOME/.local/state}"
stamp=$(date +%Y%m%d-%H%M%S)
backup="$state_home/agent-hub/install-backups/$stamp"
activate=true
install_plasma=true

usage() {
  cat <<'USAGE'
Usage: ./install-user.sh [--no-activate] [--no-plasma]

Installs the Agent Hub Python package, CLI wrapper, session service, D-Bus
activation file, and optionally the Plasma 6 widget for the current user.
Existing targets are copied to a dated backup first.
USAGE
}

while (($#)); do
  case "$1" in
    --no-activate) activate=false ;;
    --no-plasma) install_plasma=false ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

command -v rsync >/dev/null || { echo "rsync is required" >&2; exit 1; }

runtime="$data_home/agent-hub/python"
launcher="$HOME/.local/bin/agent-hub"
unit="$config_home/systemd/user/agent-hub.service"
dbus_service="$data_home/dbus-1/services/io.github.jhs88.AgentHub.service"
plasmoid="$data_home/plasma/plasmoids/io.github.jhs88.agenthub"

backup_target() {
  local path=$1
  [[ -e $path || -L $path ]] || return 0
  local relative
  if [[ $path == "$HOME"/* ]]; then
    relative="home/${path#"$HOME"/}"
  else
    relative="external/${path#/}"
  fi
  mkdir -p "$backup/$(dirname -- "$relative")"
  cp -a -- "$path" "$backup/$relative"
}

for target in "$runtime" "$launcher" "$unit" "$dbus_service"; do
  backup_target "$target"
done
if [[ $install_plasma == true ]]; then
  backup_target "$plasmoid"
fi

mkdir -p "$runtime" "$(dirname -- "$launcher")" "$(dirname -- "$unit")" "$(dirname -- "$dbus_service")"
rsync -a --delete "$root/src/agent_hub/" "$runtime/agent_hub/"
install -m 0755 "$root/contrib/bin/agent-hub" "$launcher"
install -m 0644 "$root/contrib/systemd/agent-hub.service" "$unit"
install -m 0644 "$root/contrib/dbus/io.github.jhs88.AgentHub.service" "$dbus_service"

if [[ $activate == true ]]; then
  /usr/bin/python3 -c 'import gi; gi.require_version("Gio", "2.0"); from gi.repository import Gio' >/dev/null
  systemctl --user daemon-reload
  systemctl --user enable --now agent-hub.service
fi

if [[ $install_plasma == true ]]; then
  command -v kpackagetool6 >/dev/null || { echo "kpackagetool6 is required for Plasma installation" >&2; exit 1; }
  if kpackagetool6 --type Plasma/Applet --show io.github.jhs88.agenthub >/dev/null 2>&1; then
    kpackagetool6 --type Plasma/Applet --upgrade "$root/plasma/package"
  else
    kpackagetool6 --type Plasma/Applet --install "$root/plasma/package"
  fi
fi

"$launcher" snapshot >/dev/null
printf 'Agent Hub installed.\nRuntime: %s\nBackup: %s\n' "$runtime" "$backup"
