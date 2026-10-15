#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages firefox keepassxc btop ffmpeg gpick trash-cli xorg-xrandr slop libnotify
stow_component "$component_root"
printf 'Browser, password manager, monitoring and X11 recording/color tools installed.\n'
