#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages \
    yazi \
    ueberzugpp \
    thunar \
    thunar-volman \
    tumbler \
    gvfs \
    gvfs-mtp \
    gvfs-gphoto2 \
    gvfs-smb \
    udisks2 \
    file-roller \
    imv \
    mpv \
    zathura \
    tesseract-data-eng \
    tesseract-data-spa \
    zathura-pdf-mupdf \
    7zip \
    fd \
    jq \
    poppler \
    resvg \
    ripgrep \
    wl-clipboard \
    xdg-user-dirs

install_aur_packages xdg-desktop-portal-termfilechooser-hunkyburrito-git

stow_component "$component_root"
xdg-user-dirs-update

# Re-evaluate portal priorities immediately when running inside a graphical
# user session. On a TTY the configuration is simply picked up at next login.
if systemctl --user --quiet is-active xdg-desktop-portal.service 2>/dev/null; then
    systemctl --user set-environment GTK_USE_PORTAL=1
    systemctl --user restart xdg-desktop-portal.service
fi

if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]] && command -v hyprctl >/dev/null 2>&1; then
    hyprctl reload
fi

printf 'Yazi file chooser, reliable save flow and default applications installed.\n'
