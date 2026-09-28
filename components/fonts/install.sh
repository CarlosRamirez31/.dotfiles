#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages fontconfig ttf-jetbrains-mono-nerd
stow_component "$component_root"
fc-cache -f >/dev/null
printf 'Lexend and JetBrainsMono Nerd Font installed.\n'
