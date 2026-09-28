#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages \
    neovim \
    git \
    ripgrep \
    fd \
    fzf \
    unzip \
    curl \
    make \
    gcc \
    cmake \
    nodejs \
    npm \
    python \
    python-pip \
    wl-clipboard \
    lazygit \
    dotnet-sdk \
    lua \
    luarocks \
    rust-analyzer \
    tree-sitter-cli

runtime_dir="$HOME/.config/nvim"
managed_init="$component_root/dotfiles/.config/nvim/init.lua"
resolved_init=''

if [[ -L $runtime_dir/init.lua ]]; then
    resolved_init=$(realpath -m -- "$runtime_dir/init.lua" 2>/dev/null || true)
fi

# The former standalone nvim-config checkout has its own .git directory. Move
# the whole tree aside so this installation has only the dotfiles history.
if [[ ( -e $runtime_dir || -L $runtime_dir ) && $resolved_init != "$managed_init" ]]; then
    backup="${runtime_dir}.backup.$(date +%Y%m%d-%H%M%S)"
    printf 'Backing up %s to %s\n' "$runtime_dir" "$backup"
    mv -- "$runtime_dir" "$backup"
fi

stow_component "$component_root"

# Lazy sync installs the exact plugin versions recorded by lazy-lock.json.
nvim --headless "+Lazy! sync" +qa
nvim --headless "+lua require('config.treesitter').install()" +qa

printf 'Neovim installed with the unified dotfiles configuration.\n'
