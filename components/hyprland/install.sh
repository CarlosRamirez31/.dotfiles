#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages \
    hyprland \
    xdg-desktop-portal-hyprland \
    xorg-xwayland \
    hypridle \
    hyprpolkitagent
stow_component "$component_root"

if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]] && command -v hyprctl >/dev/null 2>&1; then
    hyprctl reload
    config_errors=$(hyprctl configerrors)
    if [[ -n $config_errors ]]; then
        printf 'Hyprland reported configuration errors:\n%s\n' "$config_errors" >&2
        exit 1
    fi
    printf 'Active Hyprland session refreshed.\n'
else
    printf 'Hyprland configuration will load at the next login.\n'
fi
