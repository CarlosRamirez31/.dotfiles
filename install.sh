#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

# This order is intentional: system services first, visual assets second,
# applications third, and the compositor last so every referenced command is
# ready when Hyprland reloads.
available_components=(
    system
    themes
    fonts
    shell
    fastfetch
    maintenance
    git-security
    backup
    workbench
    desktop-extras
    session
    desktop-tools
    files
    hardware
    security
    uwsm
    alacritty
    nvim
    rofi
    wallpaper
    hyprpanel
    hyprland
    doctor
)

usage() {
    printf 'Usage: %s [all|COMPONENT ...]\n' "${0##*/}"
    printf 'Components (default order): %s\n' "${available_components[*]}"
}

component_exists() {
    local requested=$1
    local component
    for component in "${available_components[@]}"; do
        [[ $component == "$requested" ]] && return 0
    done
    return 1
}

if (( $# == 1 )) && [[ $1 == --help || $1 == -h ]]; then
    usage
    exit 0
fi

if (( $# == 0 )) || { (( $# == 1 )) && [[ $1 == all ]]; }; then
    selected_components=("${available_components[@]}")
else
    requested_components=("$@")
    for requested in "${requested_components[@]}"; do
        if ! component_exists "$requested"; then
            printf 'Unknown component: %s\n' "$requested" >&2
            usage >&2
            exit 2
        fi
    done

    # Normalize a partial installation to the same dependency-safe order used
    # by a full installation, regardless of the argument order.
    selected_components=()
    for component in "${available_components[@]}"; do
        for requested in "${requested_components[@]}"; do
            if [[ $component == "$requested" ]]; then
                selected_components+=("$component")
                break
            fi
        done
    done
fi

for component in "${selected_components[@]}"; do
    if ! component_exists "$component"; then
        printf 'Unknown component: %s\n' "$component" >&2
        usage >&2
        exit 2
    fi

    installer="$repo_root/components/$component/install.sh"
    if [[ ! -x $installer ]]; then
        printf 'Component installer is missing or not executable: %s\n' "$installer" >&2
        exit 1
    fi

    printf '\n==> Installing %s\n' "$component"
    "$installer"
done

printf '\nSetup complete.\n'
printf 'On a fresh installation, reboot and select "Hyprland (uwsm-managed)".\n'
printf 'Terminal: Ctrl+Alt+T or Super+Enter | Launcher: Super+Space or Alt+F2\n'
printf 'Validate later with: dotfiles-doctor\n'
