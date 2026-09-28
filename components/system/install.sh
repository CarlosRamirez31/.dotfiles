#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user

packages=(
    git
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

needs_display_manager=false
if ! systemctl is-enabled display-manager.service >/dev/null 2>&1; then
    packages+=(sddm)
    needs_display_manager=true
fi

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

if [[ $needs_display_manager == true ]]; then
    sudo systemctl enable sddm.service
else
    printf 'Keeping the currently enabled display manager.\n'
fi

printf 'Base desktop services installed and configured.\n'
