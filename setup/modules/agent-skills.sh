#!/usr/bin/env bash
set -euo pipefail
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"
require_arch_user
install_packages python
link_component "agent-skills"
"$DOTFILES_ROOT/bin/dotfiles-agent-skills"
printf 'Skills compartidas instaladas. Usa --hub y --hermes dev-podman para las integraciones opcionales.\n'
