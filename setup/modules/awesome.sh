#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"
require_arch_user
install_packages awesome picom mesa-utils xorg-server xorg-xrandr xorg-xrdb xorg-xset xorg-setxkbmap xkeyboard-config python-gobject python-cairo gtk3
# Recent NVIDIA GPUs use NVK + Zink for OpenGL when Nouveau is active.
# Without its Vulkan driver Xorg can fall back to software on external outputs.
if compgen -G '/sys/bus/pci/drivers/nouveau/????:??:??.?' >/dev/null; then
    install_packages vulkan-nouveau
fi
link_component "awesome"
printf 'AwesomeWM X11 session and Picom configuration installed.\n'
