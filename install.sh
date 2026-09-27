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
hyprpanel_template="$repo_root/templates/hyprpanel/config.json"

if [[ ! -d $package_root/.config/hypr ]]; then
    printf 'The Hyprland Stow package was not found in %s.\n' "$package_root" >&2
    exit 1
fi

if [[ ! -f $hyprpanel_template ]]; then
    printf 'The HyprPanel template was not found in %s.\n' "$hyprpanel_template" >&2
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
    ghostty
    rofi
    awww
    hypridle
    hyprpolkitagent
    pipewire
    pipewire-pulse
    wireplumber
    networkmanager
    brightnessctl
    pacman-contrib
    playerctl
    upower
    ttf-jetbrains-mono-nerd
)

aur_packages=(
    ags-hyprpanel-git
    bibata-cursor-theme
    oranchelo-icon-theme-git
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

missing_aur_packages=()
for package in "${aur_packages[@]}"; do
    if ! pacman -Q "$package" >/dev/null 2>&1; then
        missing_aur_packages+=("$package")
    fi
done

aur_helper=""
if command -v paru >/dev/null 2>&1; then
    aur_helper=paru
elif command -v yay >/dev/null 2>&1; then
    aur_helper=yay
fi

if (( ${#missing_aur_packages[@]} > 0 )) && [[ -z $aur_helper ]]; then
    if ! pacman -Q base-devel >/dev/null 2>&1; then
        missing_packages+=(base-devel)
    fi
fi

if (( ${#missing_packages[@]} > 0 )); then
    printf 'Installing missing packages: %s\n' "${missing_packages[*]}"
    sudo pacman -Syu --needed "${missing_packages[@]}"
else
    printf 'All required packages are already installed.\n'
fi

if (( ${#missing_aur_packages[@]} > 0 )); then
    if [[ -z $aur_helper ]]; then
        build_root=$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-yay.XXXXXX")
        printf 'Installing the AUR helper yay-bin...\n'
        git clone --depth=1 https://aur.archlinux.org/yay-bin.git "$build_root/yay-bin"
        (
            cd "$build_root/yay-bin"
            makepkg -si --needed --noconfirm
        )
        rm -rf -- "$build_root"
        aur_helper=yay
    fi

    printf 'Installing missing AUR packages: %s\n' "${missing_aur_packages[*]}"
    "$aur_helper" -S --needed --noconfirm "${missing_aur_packages[@]}"
else
    printf 'All required AUR packages are already installed.\n'
fi

for required_command in ghostty rofi uwsm hyprpanel; do
    if ! command -v "$required_command" >/dev/null 2>&1; then
        printf 'Required command not found after installation: %s\n' "$required_command" >&2
        exit 1
    fi
done

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
    "$HOME/.config/ghostty" \
    "$HOME/.config/rofi" \
    "$HOME/.config/uwsm" \
    "$HOME/.config/wallpapers" \
    "$HOME/.local/share/fonts/Lexend"; do
    backup_unmanaged_path "$target"
done

# HyprPanel owns generated files in this directory. Back up a pre-existing
# foreign configuration once, then update our template in place on later runs.
hyprpanel_runtime="$HOME/.config/hyprpanel"
hyprpanel_marker="$hyprpanel_runtime/.managed-by-dotfiles"
if [[ -d $hyprpanel_runtime && ! -f $hyprpanel_marker ]]; then
    backup_unmanaged_path "$hyprpanel_runtime"
fi

printf 'Linking the managed configuration...\n'
stow --dir="$repo_root" --target="$HOME" --restow hypr

# HyprPanel rewrites its configuration and creates generated module files.
# Keep those runtime files outside the Git worktree.
if [[ -L $hyprpanel_runtime ]]; then
    rm -- "$hyprpanel_runtime"
fi
mkdir -p -- "$hyprpanel_runtime"
install -m 0644 -- "$hyprpanel_template" "$hyprpanel_runtime/config.json"
touch -- "$hyprpanel_marker"

fc-cache -f >/dev/null

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

    # Stop the old panel if this machine used an earlier revision.
    systemctl --user stop waybar.service >/dev/null 2>&1 || true
    pkill -x waybar >/dev/null 2>&1 || true

    pkill -x hyprpanel >/dev/null 2>&1 || true
    pkill -f '/usr/share/hyprpanel/hyprpanel.js' >/dev/null 2>&1 || true
    nohup uwsm app -- hyprpanel \
        >"${XDG_RUNTIME_DIR:-/tmp}/hyprpanel-dotfiles.log" 2>&1 &

    if ! pgrep -x awww-daemon >/dev/null 2>&1; then
        nohup awww-daemon \
            >"${XDG_RUNTIME_DIR:-/tmp}/awww-dotfiles.log" 2>&1 &
    fi
    awww img "$HOME/.config/wallpapers/arch-bsod.png" \
        --transition-type none >/dev/null 2>&1 || true

    hyprctl setcursor Bibata-Modern-Classic 24 >/dev/null 2>&1 || true

    printf 'Hyprland, HyprPanel and the wallpaper were refreshed.\n'
else
    printf 'The configuration will load on the next Hyprland login.\n'
fi

printf '\nSetup complete.\n'
printf 'On a fresh installation, reboot and select "Hyprland (uwsm-managed)".\n'
printf 'Terminal: Ctrl+Alt+T or Super+Enter | Launcher: Super+Space or Alt+F2\n'
