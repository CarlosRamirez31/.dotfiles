#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages kitty zsh ttf-jetbrains-mono-nerd noto-fonts-emoji
link_component "kitty"
printf 'Kitty installed and configured.\n'
