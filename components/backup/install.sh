#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages restic
stow_component "$component_root"
systemctl --user daemon-reload

if [[ -s $HOME/.config/dotfiles/backup.conf ]]; then
    systemctl --user enable --now dotfiles-backup.timer
    printf 'Restic backup timer enabled for the configured repository.\n'
else
    printf 'Restic installed. Configure its destination with: backup setup REPOSITORY\n'
fi
