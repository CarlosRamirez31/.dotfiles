#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user

for tool in distrobox podman; do
    if ! command -v "$tool" >/dev/null; then
        printf 'Falta %s. Ejecuta: ./install.sh workbench flutter\n' "$tool" >&2
        exit 1
    fi
done

if podman container exists dev; then
    :
else
    status=$?
    if [[ $status != 1 ]]; then
        printf 'No se pudo consultar Podman (código %s); no se creará ningún contenedor.\n' "$status" >&2
        exit "$status"
    fi
    distrobox assemble create --file "$component_root/../workbench/dotfiles/.config/distrobox/distrobox.ini" --name dev
fi

distrobox enter dev -- bash "$component_root/setup-container.sh"
# Enable PATH and the launcher only after the optional setup succeeds.
stow_component "$component_root"
printf 'Flutter activado en dev. Vuelve a entrar en dev y abre Neovim allí.\n'
