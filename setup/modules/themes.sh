#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_aur_packages bibata-cursor-theme oranchelo-icon-theme-git
printf 'Cursor and icon themes installed.\n'
