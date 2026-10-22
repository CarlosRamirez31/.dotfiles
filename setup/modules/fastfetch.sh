#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages fastfetch
link_component "fastfetch"

fastfetch --config "$DOTFILES_ROOT/config/fastfetch/config.jsonc" --pipe false >/dev/null
printf 'Fastfetch installed. Run "fastfetch" or open a new Zsh terminal.\n'
