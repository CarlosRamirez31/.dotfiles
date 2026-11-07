#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
virtualization=$(systemd-detect-virt --vm 2>/dev/null || true)
packages=(bluez bluez-utils)
if [[ $virtualization == none ]]; then
    packages+=(fwupd smartmontools)
fi
install_packages "${packages[@]}"

# The RTX 4050 Laptop uses NVIDIA's open kernel module with the stock kernel.
# Leave other GPUs and kernel variants to their own driver configuration.
for device in /sys/bus/pci/devices/*; do
    [[ -r $device/vendor && -r $device/device ]] || continue
    if [[ $(<"$device/vendor") == 0x10de && $(<"$device/device") == 0x28e1 ]]; then
        if pacman -Q linux >/dev/null 2>&1; then
            install_packages nvidia-open nvidia-utils
            sudo mkinitcpio -P
            printf 'RTX 4050 Laptop driver configured; reboot to activate it.\n'
        else
            printf 'RTX 4050 Laptop detected without the stock linux kernel; NVIDIA driver configuration left unchanged.\n'
        fi
        break
    fi
done

link_component "hardware"
systemctl --user daemon-reload
systemctl --user enable dotfiles-touchpad-typing.service

if [[ $virtualization == none ]] || compgen -G '/sys/class/bluetooth/hci*' >/dev/null; then
    sudo systemctl enable --now bluetooth.service
else
    printf 'Virtual machine without a Bluetooth controller; service left disabled.\n'
fi

if [[ $virtualization == none ]]; then
    sudo systemctl enable --now fwupd-refresh.timer smartd.service
    printf 'Firmware refresh and disk health monitoring enabled.\n'
fi

printf 'Bluetooth tools installed; use the desktop panel or bluetoothctl to pair devices.\n'
