#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages maim slop xclip clipmenu rofi libnotify xdotool xorg-xprop python
link_component "desktop-tools"

printf 'Screenshots, clipboard history and desktop shortcuts installed.\n'
