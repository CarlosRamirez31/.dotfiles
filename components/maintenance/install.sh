#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages pacman-contrib
stow_component "$component_root"

sudo systemctl enable --now paccache.timer fstrim.timer
printf 'Safe maintenance checks and weekly cache/TRIM timers installed.\n'
