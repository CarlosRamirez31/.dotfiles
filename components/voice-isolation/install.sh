#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user
install_packages pipewire pipewire-pulse wireplumber libpulse python python-pip python-gobject gtk3 git noise-suppression-for-voice
stow_component "$component_root"
systemctl --user daemon-reload
systemctl --user disable --now dotfiles-microphone.service
systemctl --user enable dotfiles-voice-isolation.service
systemctl --user restart dotfiles-voice-isolation.service
"$HOME/.local/bin/dotfiles-microphone" cleanup-legacy
printf 'Entrada habitual: Aislamiento de voz. Solo mi voz se inicia manualmente desde dotfiles-microphone y usa una entrada experimental separada.\n'
