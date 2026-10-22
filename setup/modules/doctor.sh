#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
link_component "doctor"
printf 'Running the final desktop health check…\n'
"$HOME/.local/bin/dotfiles-doctor"
