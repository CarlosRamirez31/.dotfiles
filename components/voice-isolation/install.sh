#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user
install_packages pipewire pipewire-pulse wireplumber libpulse python python-pip python-gobject gtk3 git noise-suppression-for-voice
stow_component "$component_root"
systemctl --user daemon-reload
systemctl --user enable dotfiles-voice-isolation.service dotfiles-microphone.service
systemctl --user restart dotfiles-voice-isolation.service
"$HOME/.local/bin/dotfiles-microphone" cleanup-legacy
if python3 -c 'import json, os, pathlib, sys; p = pathlib.Path(os.getenv("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")) / "voice-isolation/microphone.json"; sys.exit(not (p.exists() and json.loads(p.read_text()).get("personal", False)))'; then
    "$HOME/.local/bin/dotfiles-microphone" personal on
else
    systemctl --user stop dotfiles-microphone.service
fi
printf 'Entrada habitual: Aislamiento de voz. Solo mi voz conserva el perfil y el estado guardados y usa Microfono solo mi voz.\n'
