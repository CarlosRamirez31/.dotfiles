#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
# Select the OCI provider explicitly so Pacman does not prompt for one of the
# providers of Podman's virtual oci-runtime dependency.
install_packages crun podman

# Remove only the obsolete links previously managed by this component. User
# files at those paths are deliberately left alone.
for legacy_path in \
    "$HOME/.config/distrobox/distrobox.ini" \
    "$HOME/.local/libexec/dotfiles-distrobox-bootstrap"; do
    if [[ -L $legacy_path && $(realpath -m -- "$legacy_path") == "$component_root"/* ]]; then
        rm -- "$legacy_path"
    fi
done

stow_component "$component_root"

printf 'Podman lab configuration installed. Build an image with: labbox build kali\n'
