#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user
install_packages pipewire pipewire-pulse wireplumber libpulse python noise-suppression-for-voice
stow_component "$component_root"
systemctl --user daemon-reload
systemctl --user enable dotfiles-voice-isolation.service
systemctl --user restart dotfiles-voice-isolation.service
printf 'Aislamiento de voz activado. Selecciona Aislamiento de voz en tus aplicaciones.\n'
