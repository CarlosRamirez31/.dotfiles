#!/usr/bin/env bash
set -euo pipefail
component_root=$1
component=$(basename -- "$component_root")
source "$component_root/../../scripts/lib.sh"
require_arch_user
controller=$component_root/../workbench/dotfiles/.local/bin/dotfiles-podman
case $component_root in
    "$HOME"/*) internal_root="/host-home/${component_root#"$HOME"/}" ;;
    *) printf 'El repositorio debe estar dentro del home compartido.\n' >&2; exit 1 ;;
esac
# The controller validates ownership and requires the existing new dev.
# Never recreate a Distrobox or install packages on the host.
"$controller" exec dev -- env FLUTTER_AVD_KEYBOARD="${FLUTTER_AVD_KEYBOARD:-yes}" \
    bash "$internal_root/setup-container.sh" "$internal_root"
if [[ $component == hermes ]]; then
    "$controller" exec dev -- python3 "$internal_root/../workbench/podman/adapt_presentation.py"
fi
stow_component "$component_root/../workbench"
stow_component "$component_root"
"$controller" integrate dev
printf '%s disponible en dev-podman.\n' "$component"
