#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages fontconfig ttf-jetbrains-mono-nerd ttf-iosevka-nerd ttf-material-icons noto-fonts-emoji
link_component "fonts"
fc-cache -f >/dev/null
printf 'Lexend, JetBrainsMono, Iosevka Nerd Font, Material Icons and emoji fallback installed.\n'
