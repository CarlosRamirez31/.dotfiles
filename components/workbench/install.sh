#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages podman distrobox
stow_component "$component_root"

systemctl --user enable --now podman.socket
if ! grep -q "^$(id -un):" /etc/subuid /etc/subgid 2>/dev/null; then
    printf 'Warning: subordinate UID/GID ranges are missing; rootless containers may require a new login.\n' >&2
fi
printf 'Rootless Podman and Distrobox workbenches installed.\n'
