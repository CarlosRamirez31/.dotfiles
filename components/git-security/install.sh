#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages git openssh libsecret gnome-keyring
stow_component "$component_root"
systemctl --user enable --now gnome-keyring-daemon.socket

if ! git config --global --get user.email >/dev/null 2>&1; then
    printf 'Git safety defaults installed. Configure identity with:\n'
    printf '  git identity setup "Your Name" email@example.com [SSH_PUBLIC_KEY]\n'
else
    printf 'Git safety defaults installed; existing global identity preserved.\n'
fi
