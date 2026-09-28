#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages gnome-keyring libsecret seahorse gcr-4 nftables
stow_component "$component_root"

systemctl --user daemon-reload
systemctl --user enable --now gnome-keyring-daemon.socket gcr-ssh-agent.socket

if [[ -n ${SSH_CONNECTION:-} ]]; then
    printf 'Remote SSH installation detected; firewall files were installed but not activated.\n'
    printf 'Run dotfiles-firewall enable locally after checking your access.\n'
else
    "$HOME/.local/bin/dotfiles-firewall" enable
fi

printf 'Keyring, SSH agent and workstation firewall installed.\n'
