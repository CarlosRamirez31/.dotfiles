#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user

for tool in distrobox podman; do
    if ! command -v "$tool" >/dev/null; then
        printf 'Falta %s. Ejecuta: ./install.sh workbench rider\n' "$tool" >&2
        exit 1
    fi
done
if podman container exists dev; then
    :
else
    status=$?
    if [[ $status != 1 ]]; then
        printf 'No se pudo consultar Podman (código %s).\n' "$status" >&2
        exit "$status"
    fi
    distrobox assemble create --file "$component_root/../workbench/dotfiles/.config/distrobox/distrobox.ini" --name dev
fi

distrobox enter dev -- bash "$component_root/setup-container.sh"
stow_component "$component_root"
printf 'Rider instalado en dev. Abre tu proyecto con: rider .\n'
