#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages firefox keepassxc btop wf-recorder hyprpicker trash-cli
stow_component "$component_root"
printf 'Browser, password manager, monitoring and Wayland utilities installed.\n'
