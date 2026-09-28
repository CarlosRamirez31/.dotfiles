#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages bluez bluez-utils blueman

virtualization=$(systemd-detect-virt --vm 2>/dev/null || true)
if [[ $virtualization == none ]] || compgen -G '/sys/class/bluetooth/hci*' >/dev/null; then
    sudo systemctl enable --now bluetooth.service
else
    printf 'Virtual machine without a Bluetooth controller; service left disabled.\n'
fi

printf 'Bluetooth tools installed; use the panel or blueman-manager to pair devices.\n'
