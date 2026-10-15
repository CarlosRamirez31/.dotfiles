#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user

packages=(
    git
    sddm
    xdg-desktop-portal-gtk
    libnotify
    pipewire
    pipewire-pulse
    wireplumber
    networkmanager
    openvpn
    brightnessctl
    pacman-contrib
    playerctl
    upower
)

virtualization=$(systemd-detect-virt --vm 2>/dev/null || true)
case $virtualization in
    vmware) packages+=(open-vm-tools) ;;
    oracle) packages+=(virtualbox-guest-utils) ;;
    kvm | qemu) packages+=(spice-vdagent) ;;
esac

install_packages "${packages[@]}"
sudo systemctl enable --now NetworkManager.service

case $virtualization in
    vmware)
        sudo systemctl enable --now vmtoolsd.service
        sudo systemctl enable --now vmware-vmblock-fuse.service
        ;;
    oracle)
        sudo systemctl enable --now vboxservice.service
        ;;
esac

current_display_manager=$(readlink -f /etc/systemd/system/display-manager.service 2>/dev/null || true)
if [[ -n $current_display_manager && $current_display_manager != */sddm.service ]]; then
    current_display_manager=${current_display_manager##*/}
    printf 'Selecting SDDM for the next boot (current session stays active; replacing %s).\n' "$current_display_manager"
    sudo systemctl disable "$current_display_manager"
fi
sudo systemctl enable sddm.service

printf 'Base desktop services installed and configured.\n'
