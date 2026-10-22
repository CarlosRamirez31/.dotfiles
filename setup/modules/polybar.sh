#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"
require_arch_user
install_packages polybar bluez bluez-utils python-gobject
sudo systemctl enable --now bluetooth.service
link_component "polybar"
printf 'ZProger Polybar top menu installed.\n'
