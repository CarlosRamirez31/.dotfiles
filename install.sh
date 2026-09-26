#!/usr/bin/env bash

set -euo pipefail

if [[ ${EUID} -eq 0 ]]; then
    printf 'Run this installer as your regular user, not as root.\n' >&2
    exit 1
fi

if ! command -v pacman >/dev/null 2>&1; then
    printf 'This installer supports Arch Linux and pacman only.\n' >&2
    exit 1
fi

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
package_root="$repo_root/hypr"

if [[ ! -d $package_root/.config/hypr ]]; then
    printf 'The Hyprland Stow package was not found in %s.\n' "$package_root" >&2
    exit 1
fi

packages=(
    git
    stow
    hyprland
    uwsm
    xdg-desktop-portal-hyprland
    xdg-desktop-portal-gtk
    xorg-xwayland
    foot
    rofi
    waybar
    awww
    hyprpolkitagent
    pipewire
    pipewire-pulse
    wireplumber
    networkmanager
    ttf-jetbrains-mono-nerd
)

needs_display_manager=false
if ! systemctl is-enabled display-manager.service >/dev/null 2>&1; then
    packages+=(sddm)
    needs_display_manager=true
fi

missing_packages=()
for package in "${packages[@]}"; do
    if ! pacman -Q "$package" >/dev/null 2>&1; then
        missing_packages+=("$package")
    fi
done

if (( ${#missing_packages[@]} > 0 )); then
    printf 'Installing missing packages: %s\n' "${missing_packages[*]}"
    sudo pacman -Syu --needed "${missing_packages[@]}"
else
    printf 'All required packages are already installed.\n'
fi

backup_stamp=$(date +%Y%m%d-%H%M%S)

is_managed_link() {
    local target=$1
    local resolved

    [[ -L $target ]] || return 1
    resolved=$(readlink -f -- "$target")
    [[ $resolved == "$package_root"/* ]]
}

backup_unmanaged_path() {
    local target=$1
    local backup

    [[ -e $target || -L $target ]] || return 0
    is_managed_link "$target" && return 0

    backup="${target}.backup.${backup_stamp}"
    printf 'Backing up %s to %s\n' "$target" "$backup"
    mv -- "$target" "$backup"
}

mkdir -p -- "$HOME/.config"

for target in \
    "$HOME/.config/hypr" \
    "$HOME/.config/foot" \
    "$HOME/.config/rofi" \
    "$HOME/.config/waybar" \
    "$HOME/.config/uwsm"; do
    backup_unmanaged_path "$target"
done

printf 'Linking the managed configuration...\n'
stow --dir="$repo_root" --target="$HOME" --restow hypr

if ! systemctl is-enabled NetworkManager.service >/dev/null 2>&1; then
    printf 'Enabling NetworkManager...\n'
    sudo systemctl enable NetworkManager.service
fi

if ! systemctl is-active NetworkManager.service >/dev/null 2>&1; then
    printf 'Starting NetworkManager...\n'
    sudo systemctl start NetworkManager.service
fi

if [[ $needs_display_manager == true ]]; then
    printf 'Enabling SDDM for the next boot...\n'
    sudo systemctl enable sddm.service
else
    printf 'Keeping the currently enabled display manager.\n'
fi

if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]] && command -v hyprctl >/dev/null 2>&1; then
    printf 'Refreshing the active Hyprland session...\n'
    hyprctl reload full-reset

    config_errors=$(hyprctl configerrors)
    if [[ -n $config_errors ]]; then
        printf 'Hyprland reported configuration errors:\n%s\n' "$config_errors" >&2
        exit 1
    fi

    systemctl --user stop waybar.service >/dev/null 2>&1 || true
    pkill -x waybar >/dev/null 2>&1 || true
    nohup waybar \
        -c "$HOME/.config/waybar/config.jsonc" \
        -s "$HOME/.config/waybar/style.css" \
        >"${XDG_RUNTIME_DIR:-/tmp}/waybar-dotfiles.log" 2>&1 &

    if ! pgrep -x awww-daemon >/dev/null 2>&1; then
        nohup awww-daemon \
            >"${XDG_RUNTIME_DIR:-/tmp}/awww-dotfiles.log" 2>&1 &
    fi
    awww clear 11111b >/dev/null 2>&1 || true

    printf 'Hyprland and Waybar were refreshed.\n'
else
    printf 'The configuration will load on the next Hyprland login.\n'
fi

printf '\nSetup complete.\n'
printf 'On a fresh installation, reboot and select "Hyprland (uwsm-managed)".\n'
printf 'Terminal: Ctrl+Alt+T | Launcher: Alt+F2\n'
