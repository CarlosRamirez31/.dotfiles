#!/usr/bin/env bash
set -euo pipefail
[[ ${CONTAINER_ID:-} == dev && -e /run/.containerenv ]] || {
    printf 'Se requiere Distrobox dev.\n' >&2
    exit 1
}
missing=()
for package in docker docker-compose docker-buildx lazydocker; do
    pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
done
if ((${#missing[@]})); then sudo pacman -Syu --needed --noconfirm "${missing[@]}"; fi
# A user-local fallback also makes the general TUI available when the host
# package has not yet been provisioned by the workbench component.
install -Dm755 /usr/bin/lazydocker "$HOME/.local/libexec/lazydocker/lazydocker"
