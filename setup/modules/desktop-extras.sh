#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages firefox keepassxc btop ffmpeg gpick trash-cli xorg-xrandr slop libnotify
link_component "desktop-extras"
printf 'Browser, password manager, monitoring and X11 recording/color tools installed.\n'
