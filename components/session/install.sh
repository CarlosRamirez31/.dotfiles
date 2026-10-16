#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages xsecurelock xss-lock xorg-xset

if compgen -G '/sys/class/power_supply/BAT*' >/dev/null; then
    if pacman -Q tlp >/dev/null 2>&1; then
        printf 'TLP is installed; keeping it as the power manager.\n'
    else
        install_packages power-profiles-daemon
        sudo systemctl enable --now power-profiles-daemon.service
    fi
else
    printf 'No laptop battery detected; skipping power-profiles-daemon.\n'
fi

stow_component "$component_root"
printf 'X11 lock screen, idle handling and safe suspend rules installed.\n'
