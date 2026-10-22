#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$repo_root/setup/lib.sh"

# This order is intentional: system services first, visual assets second,
# applications third, and Awesome last so every referenced command is ready
# when the X11 session starts.
default_components=(
    system
    sddm
    themes
    fonts
    shell
    fastfetch
    maintenance
    quality
    git-security
    backup
    workbench
    desktop-extras
    session
    desktop-tools
    files
    hardware
    security
    alacritty
    nvim
    rofi
    wallpaper
    awesome
    polybar
    doctor
)
optional_components=(hermes flutter rider docker dbeaver voice-isolation)
available_components=("${default_components[@]}" "${optional_components[@]}")

usage() {
    printf 'Usage: %s [--dry-run] [all|COMPONENT ...]\n' "${0##*/}"
    printf 'Components installed by default: %s\n' "${default_components[*]}"
    printf 'Optional (explicit selection only): %s\n' "${optional_components[*]}"
}

component_exists() {
    local requested=$1
    local component
    for component in "${available_components[@]}"; do
        [[ $component == "$requested" ]] && return 0
    done
    return 1
}

dry_run=false
requested_args=()
for argument in "$@"; do
    if [[ $argument == --dry-run ]]; then dry_run=true; else requested_args+=("$argument"); fi
done
set -- "${requested_args[@]}"

if (($# == 1)) && [[ $1 == --help || $1 == -h ]]; then
    usage
    exit 0
fi

if (($# == 0)) || { (($# == 1)) && [[ $1 == all ]]; }; then
    selected_components=("${default_components[@]}")
else
    requested_components=()
    for argument in "$@"; do
        if [[ $argument == all ]]; then requested_components+=("${default_components[@]}"); else requested_components+=("$argument"); fi
    done
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

component_installer() {
    local installer="$repo_root/setup/modules/$1.sh"
    [[ -f $installer ]] || installer="$repo_root/setup/modules/$1/install.sh"
    printf '%s\n' "$installer"
}

# Fail before sudo or package transactions if any selected entry point is absent.
for component in "${selected_components[@]}"; do
    installer=$(component_installer "$component")
    if [[ ! -x $installer ]]; then
        printf 'Component installer is missing or not executable: %s\n' "$installer" >&2
        exit 1
    fi
done

if [[ $dry_run == true ]]; then
    printf 'Selected components: %s\n' "${selected_components[*]}"
    exit 0
fi

require_arch_user
printf '\n==> Authenticating sudo for the installation\n'
sudo -v
(
    while sudo -n -v 2>/dev/null; do
        sleep 60
    done
) &
sudo_keepalive_pid=$!
cleanup() {
    kill "$sudo_keepalive_pid" 2>/dev/null || true
    wait "$sudo_keepalive_pid" 2>/dev/null || true
}
trap cleanup EXIT

for component in "${selected_components[@]}"; do
    if ! component_exists "$component"; then
        printf 'Unknown component: %s\n' "$component" >&2
        usage >&2
        exit 2
    fi

    installer=$(component_installer "$component")
    if [[ ! -x $installer ]]; then
        printf 'Component installer is missing or not executable: %s\n' "$installer" >&2
        exit 1
    fi

    printf '\n==> Installing %s\n' "$component"
    "$installer"
done

printf '\nSetup complete.\n'
printf 'On a fresh installation, reboot and select "Awesome" in your login manager.\n'
printf 'Terminal: Ctrl+Alt+T or Alt+Enter | Launcher: Alt+Space or Alt+F2\n'
printf 'Validate later with: doctor\n'
