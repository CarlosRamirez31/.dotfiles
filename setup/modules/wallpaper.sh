#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages feh imagemagick
link_component "wallpaper"
mkdir -p -- "$HOME/Pictures/Wallpapers"

# The optional native picker/renderer live in separate repositories.
if [[ -f "$HOME/Documents/Programacion/qs-wallpaper-picker/scripts/steam_library.py" ]]; then
    systemctl --user daemon-reload
    systemctl --user enable --now bollow-wallpaper-sync.path
    systemctl --user enable bollow-wallpaper-sync.service
fi
"$HOME/.local/bin/dotfiles-wallpaper" restore || true

printf 'Wallpaper installed and configured.\n'
