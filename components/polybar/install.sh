#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user
install_packages polybar
stow_component "$component_root"
printf 'ZProger Polybar top menu installed.\n'
