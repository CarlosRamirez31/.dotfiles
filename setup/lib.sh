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

# Link individual files so optional modules can share a destination directory.
# All sources and destinations are declared explicitly in links.tsv.
link_component() {
    local component=$1
    local owner source_relative target_relative source_file target resolved backup
    local -a sources=() targets=()

    # Validate the entire selection before changing any destination.
    while IFS=$'\t' read -r owner source_relative target_relative; do
        [[ $owner == "$component" ]] || continue
        case /$source_relative/ in */../* | */./* | //*)
            printf 'Invalid source in links.tsv: %s\n' "$source_relative" >&2
            return 1
            ;;
        esac
        case /$target_relative/ in */../* | */./* | //*)
            printf 'Invalid target in links.tsv: %s\n' "$target_relative" >&2
            return 1
            ;;
        esac
        source_file="$DOTFILES_ROOT/$source_relative"
        if [[ ! -f $source_file || -z $target_relative ]]; then
            printf 'Invalid link entry: %s\n' "$source_relative" >&2
            return 1
        fi
        sources+=("$source_file")
        targets+=("$HOME/$target_relative")
    done <"$DOTFILES_ROOT/setup/links.tsv"

    local index
    for index in "${!sources[@]}"; do
        source_file=${sources[index]}
        target=${targets[index]}
        # A parent directory may itself point into the repository. Never move
        # the source file aside while trying to replace its installed alias.
        [[ $target -ef $source_file ]] && continue
        if [[ -L $target ]]; then
            resolved=$(realpath -m -- "$target")
            [[ $resolved == "$source_file" ]] && continue
            if [[ $resolved == "$DOTFILES_ROOT"/* ]]; then
                rm -- "$target"
            fi
        fi
        mkdir -p -- "$(dirname -- "$target")"
        if [[ -e $target || -L $target ]]; then
            backup="${target}.backup.$(date +%Y%m%d-%H%M%S).$$"
            while [[ -e $backup || -L $backup ]]; do backup+=.backup; done
            printf 'Backing up %s to %s\n' "$target" "$backup"
            mv -- "$target" "$backup"
        fi
        ln -s -- "$source_file" "$target"
    done
}
