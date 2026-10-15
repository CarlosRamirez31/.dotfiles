#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages maim slop xclip clipmenu flameshot rofi libnotify
stow_component "$component_root"
systemctl --user disable --now dotfiles-cliphist-text.service dotfiles-cliphist-image.service 2>/dev/null || true

printf 'Screenshots, clipboard history and desktop shortcuts installed.\n'
