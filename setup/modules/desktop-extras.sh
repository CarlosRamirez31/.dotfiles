#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages firefox keepassxc btop gpick trash-cli libnotify
install_aur_packages limusic-bin
link_component "desktop-extras"
printf 'Browser, music player, password manager, monitoring, color picker and trash tools installed.\n'
