#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages grim slurp swappy cliphist wl-clipboard
stow_component "$component_root"

systemctl --user daemon-reload
systemctl --user enable dotfiles-cliphist-text.service dotfiles-cliphist-image.service
if [[ -n ${WAYLAND_DISPLAY:-} ]]; then
    systemctl --user restart dotfiles-cliphist-text.service dotfiles-cliphist-image.service
fi

printf 'Screenshots, clipboard history and desktop shortcuts installed.\n'
