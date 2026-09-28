#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_aur_packages ags-hyprpanel-git

runtime_dir="$HOME/.config/hyprpanel"
marker="$runtime_dir/.managed-by-dotfiles"
if [[ ( -e $runtime_dir || -L $runtime_dir ) && ! -f $marker ]]; then
    backup="${runtime_dir}.backup.$(date +%Y%m%d-%H%M%S)"
    printf 'Backing up %s to %s\n' "$runtime_dir" "$backup"
    mv -- "$runtime_dir" "$backup"
fi

mkdir -p -- "$runtime_dir"
install -m 0644 -- "$component_root/templates/config.json" "$runtime_dir/config.json"
install -m 0644 -- "$component_root/templates/modules.scss" "$runtime_dir/modules.scss"
touch -- "$marker"

if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
    systemctl --user stop waybar.service >/dev/null 2>&1 || true
    pkill -x waybar >/dev/null 2>&1 || true
    pkill -x hyprpanel >/dev/null 2>&1 || true
    if command -v uwsm-app >/dev/null 2>&1; then
        nohup uwsm-app -- hyprpanel \
            >"${XDG_RUNTIME_DIR:-/tmp}/hyprpanel-dotfiles.log" 2>&1 &
    else
        nohup hyprpanel \
            >"${XDG_RUNTIME_DIR:-/tmp}/hyprpanel-dotfiles.log" 2>&1 &
    fi
fi

printf 'HyprPanel installed and configured.\n'
