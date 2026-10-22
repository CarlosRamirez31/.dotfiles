#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

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
    xdg-user-dirs \
    xdg-desktop-portal \
    xdg-desktop-portal-gtk

link_component "files"
xdg-user-dirs-update

# Re-evaluate portal priorities immediately when running inside a graphical
# user session. On a TTY the configuration is simply picked up at next login.
if systemctl --user --quiet is-active xdg-desktop-portal.service 2>/dev/null; then
    systemctl --user set-environment GTK_USE_PORTAL=1
    systemctl --user restart xdg-desktop-portal.service
fi

printf 'GTK/X11 file chooser and default applications installed; Yazi is ready in Alacritty.\n'
