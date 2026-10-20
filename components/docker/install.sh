#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user
for tool in distrobox podman; do
    command -v "$tool" >/dev/null || {
        printf 'Ejecuta ./install.sh workbench docker\n' >&2
        exit 1
    }
done
if ! podman container exists dev; then
    distrobox assemble create --file "$component_root/../workbench/dotfiles/.config/distrobox/distrobox.ini" --name dev
fi
distrobox enter dev -- bash "$component_root/setup-container.sh"
stow_component "$component_root/../workbench"
stow_component "$component_root"
systemctl --user enable --now podman.socket
printf 'Docker CLI y Compose disponibles en dev, conectados a Podman rootless.\n'
