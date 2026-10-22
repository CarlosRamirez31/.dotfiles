#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

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

sudo systemctl enable --force sddm.service

printf 'Base desktop services installed and configured.\n'
