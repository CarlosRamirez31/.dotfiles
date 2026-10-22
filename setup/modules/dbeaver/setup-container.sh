#!/usr/bin/env bash
set -euo pipefail
[[ ${CONTAINER_ID:-} == dev && -e /run/.containerenv ]] || {
    printf 'Se requiere Distrobox dev.\n' >&2
    exit 1
}
missing=()
for package in dbeaver coreutils util-linux; do
    pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
done
if ((${#missing[@]})); then sudo pacman -Syu --needed --noconfirm "${missing[@]}"; fi
