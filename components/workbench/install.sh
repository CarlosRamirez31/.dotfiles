#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
# Select the OCI provider explicitly. Otherwise Pacman prompts on every fresh
# install to choose between crun, krun, and runc for Podman's virtual
# oci-runtime dependency. crun is lightweight and works well with rootless
# Podman; krun's KVM isolation is unnecessary for these Distrobox profiles.
install_packages crun podman distrobox lazydocker podman-compose
stow_component "$component_root"

systemctl --user enable --now podman.socket
if ! grep -q "^$(id -un):" /etc/subuid /etc/subgid 2>/dev/null; then
    printf 'Warning: subordinate UID/GID ranges are missing; rootless containers may require a new login.\n' >&2
fi
printf 'Rootless Podman and Distrobox workbenches installed.\n'
