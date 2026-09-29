#!/usr/bin/env bash

# Shared installer helpers. Component installers source this file so every
# package has the same idempotent package and dotfile behavior.

DOTFILES_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)

require_arch_user() {
    if [[ ${EUID} -eq 0 ]]; then
        printf 'Run this installer as your regular user, not as root.\n' >&2
        exit 1
    fi

    if ! command -v pacman >/dev/null 2>&1; then
        printf 'This installer supports Arch Linux and pacman only.\n' >&2
        exit 1
    fi
}

install_packages() {
    local package
    local -a missing=()

    for package in "$@"; do
        pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
    done

    if ((${#missing[@]} == 0)); then
        printf 'Packages already installed: %s\n' "$*"
        return
    fi

    printf 'Installing missing packages: %s\n' "${missing[*]}"
    # Arch does not support partial upgrades. Refresh and upgrade whenever a
    # component actually needs a package; subsequent components normally skip.
    # Keep fresh installations unattended after sudo authentication. Pacman
    # resolves virtual dependencies with the repository's current default
    # instead of opening an interactive provider selector.
    sudo pacman -Syu --needed --noconfirm "${missing[@]}"
}

find_aur_helper() {
    if command -v paru >/dev/null 2>&1; then
        printf 'paru'
    elif command -v yay >/dev/null 2>&1; then
        printf 'yay'
    fi
}

ensure_aur_helper() {
    local helper
    local build_root

    helper=$(find_aur_helper)
    if [[ -n $helper ]]; then
        AUR_HELPER=$helper
        return
    fi

    install_packages git base-devel
    build_root=$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-yay.XXXXXX")
    git clone --depth=1 https://aur.archlinux.org/yay-bin.git "$build_root/yay-bin"
    (
        cd -- "$build_root/yay-bin" || exit
        makepkg -si --needed --noconfirm
    )
    rm -rf -- "$build_root"
    AUR_HELPER=yay
}

install_aur_packages() {
    local package
    local -a missing=()

    for package in "$@"; do
        pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
    done

    if ((${#missing[@]} == 0)); then
        printf 'AUR packages already installed: %s\n' "$*"
        return
    fi

    ensure_aur_helper
    printf 'Installing missing AUR packages: %s\n' "${missing[*]}"
    "$AUR_HELPER" -S --needed --noconfirm "${missing[@]}"
}

prepare_managed_file() {
    local source_file=$1
    local relative_path=${source_file#*/dotfiles/}
    local target="$HOME/$relative_path"
    local resolved=''
    local backup

    mkdir -p -- "$(dirname -- "$target")"
    [[ -e $target || -L $target ]] || return 0

    if [[ -L $target ]]; then
        # realpath -m also resolves dangling links. This lets a reorganized
        # repository replace its old Stow links instead of preserving useless
        # broken links as backups.
        resolved=$(realpath -m -- "$target" 2>/dev/null || true)
        if [[ $resolved == "$DOTFILES_ROOT"/* ]]; then
            rm -- "$target"
            return
        fi
    fi

    backup="${target}.backup.$(date +%Y%m%d-%H%M%S)"
    printf 'Backing up %s to %s\n' "$target" "$backup"
    mv -- "$target" "$backup"
}

stow_component() {
    local component_root=$1
    local package_root="$component_root/dotfiles"
    local source_file

    if [[ ! -d $package_root ]]; then
        printf 'No dotfiles directory found in %s.\n' "$component_root" >&2
        exit 1
    fi

    install_packages stow
    while IFS= read -r -d '' source_file; do
        prepare_managed_file "$source_file"
    done < <(find "$package_root" -type f -print0)

    stow --dir="$component_root" --target="$HOME" --no-folding --restow dotfiles
}
