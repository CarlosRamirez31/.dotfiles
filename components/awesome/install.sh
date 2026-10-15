#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"
require_arch_user
install_packages awesome picom mesa-utils xorg-server xorg-xhost xorg-xinit xorg-xrandr xorg-xrdb xorg-xset xorg-xsetroot
stow_component "$component_root"
printf 'AwesomeWM X11 session and Picom configuration installed.\n'
