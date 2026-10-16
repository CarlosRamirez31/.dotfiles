#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user

# Betterlockscreen is the normal Awesome/X11 lock screen.  Keep Xsecurelock
# installed as a safe fallback, but install Betterlockscreen and every
# repository dependency its launcher checks for so it cannot silently fall
# back after a fresh `session` install.
install_packages bc xorg-xdpyinfo xorg-xset xsecurelock xss-lock
install_aur_packages betterlockscreen

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
