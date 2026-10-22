#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages restic
link_component "backup"
systemctl --user daemon-reload

if [[ -s $HOME/.config/dotfiles/backup.conf ]]; then
    systemctl --user enable --now dotfiles-backup.timer
    printf 'Weekly Restic backup enabled. A floating terminal requests the password.\n'
else
    printf 'Restic installed. Configure its destination with: backup setup REPOSITORY\n'
fi
