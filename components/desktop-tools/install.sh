#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages maim slop xclip clipmenu flameshot rofi libnotify xdotool xorg-xprop
stow_component "$component_root"

printf 'Screenshots, clipboard history and desktop shortcuts installed.\n'
