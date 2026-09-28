#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages awww
stow_component "$component_root"

if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
    if ! pgrep -x awww-daemon >/dev/null 2>&1; then
        nohup awww-daemon \
            >"${XDG_RUNTIME_DIR:-/tmp}/awww-dotfiles.log" 2>&1 &
    fi
    awww img "$HOME/.config/wallpapers/arch-bsod.png" \
        --transition-type none >/dev/null 2>&1 || true
fi

printf 'Wallpaper installed and configured.\n'
