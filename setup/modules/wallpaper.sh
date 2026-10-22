#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages feh imagemagick
link_component "wallpaper"
mkdir -p -- "$HOME/Pictures/Wallpapers"

"$HOME/.local/bin/dotfiles-wallpaper" restore || true

printf 'Wallpaper installed and configured.\n'
