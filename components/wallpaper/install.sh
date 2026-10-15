#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages feh gtk3 python-gobject
stow_component "$component_root"
mkdir -p -- "$HOME/Pictures/Wallpapers"

"$HOME/.local/bin/dotfiles-wallpaper" restore || true

printf 'Wallpaper installed and configured.\n'
