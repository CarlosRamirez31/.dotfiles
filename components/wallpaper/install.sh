#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages awww gtk-layer-shell python-gobject
install_aur_packages waypaper
stow_component "$component_root"
mkdir -p -- "$HOME/Pictures/Wallpapers"

waypaper_config="$HOME/.config/waypaper/config.ini"
if [[ ! -e $waypaper_config ]]; then
    install -Dm600 "$component_root/templates/config.ini" "$waypaper_config"
fi

old_rofi_theme="$HOME/.config/rofi/wallpaper.rasi"
if [[ -L $old_rofi_theme ]] &&
    [[ $(realpath -m -- "$old_rofi_theme") == "$component_root/dotfiles/.config/rofi/wallpaper.rasi" ]]; then
    rm -- "$old_rofi_theme"
fi

if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
    "$HOME/.local/bin/dotfiles-wallpaper" restore || true
fi

printf 'Wallpaper installed and configured.\n'
