#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

require_arch_user
install_packages shellcheck shfmt jq lua zsh python python-yaml neovim

printf 'Repository validation tools installed. Run: ./check.sh\n'
