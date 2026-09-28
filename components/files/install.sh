#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages \
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
    xdg-user-dirs

stow_component "$component_root"
xdg-user-dirs-update
printf 'File manager, removable media and default applications installed.\n'
