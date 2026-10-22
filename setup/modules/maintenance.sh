#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages pacman-contrib
link_component "maintenance"

sudo systemctl enable --now paccache.timer fstrim.timer
printf 'Safe maintenance checks and weekly cache/TRIM timers installed.\n'
