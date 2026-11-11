#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages \
    yazi \
    python-gobject \
    python-cairo \
    gtk3 \
    thunar \
    thunar-volman \
    tumbler \
    gvfs \
    gvfs-mtp \
    android-tools \
    android-udev \
    gvfs-gphoto2 \
    gvfs-smb \
    udisks2 \
    file-roller \
    imv \
    mpv \
    ffmpeg \
    imagemagick \
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

install_aur_packages xdg-desktop-portal-termfilechooser
link_component "files"
xdg-user-dirs-update

# Let the yes/no prompt own automatic mounting; manual Thunar mounts still work.
for property in /automount-drives/enabled /automount-media/enabled /autobrowse/enabled; do
    xfconf-query -c thunar-volman -p "$property" --create --type bool --set false
done
systemctl --user daemon-reload
systemctl --user enable dotfiles-removable.service
if [[ -n ${DISPLAY:-} ]]; then
    systemctl --user import-environment DISPLAY XAUTHORITY
    systemctl --user start dotfiles-removable.service
fi

# Re-evaluate portal priorities immediately when running inside a graphical
# user session. On a TTY the configuration is simply picked up at next login.
if systemctl --user --quiet is-active xdg-desktop-portal.service 2>/dev/null; then
    systemctl --user set-environment GTK_USE_PORTAL=1
    systemctl --user try-restart xdg-desktop-portal-termfilechooser.service
    systemctl --user restart xdg-desktop-portal.service
fi

printf 'GTK/X11 file chooser and default applications installed; Yazi is ready in Kitty.\n'
