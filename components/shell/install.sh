#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_packages \
    git \
    zsh \
    starship \
    eza \
    bat \
    fzf \
    fd \
    ripgrep \
    curl \
    less \
    zoxide \
    vivid \
    zsh-autosuggestions \
    zsh-syntax-highlighting \
    zsh-completions \
    zsh-history-substring-search \
    jq \
    yq \
    nmap \
    bind \
    whois \
    traceroute \
    openbsd-netcat \
    iproute2 \
    openssh \
    tcpdump \
    lsof \
    inetutils \
    man-db \
    man-pages \
    tldr

data_home=${XDG_DATA_HOME:-$HOME/.local/share}
ohmyzsh_dir="$data_home/oh-my-zsh"

if [[ -d $ohmyzsh_dir/.git ]]; then
    printf 'Oh My Zsh is already installed in %s; skipping.\n' "$ohmyzsh_dir"
elif [[ -e $ohmyzsh_dir ]]; then
    backup="${ohmyzsh_dir}.backup.$(date +%Y%m%d-%H%M%S)"
    printf 'Backing up %s to %s\n' "$ohmyzsh_dir" "$backup"
    mv -- "$ohmyzsh_dir" "$backup"
    git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$ohmyzsh_dir"
else
    git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$ohmyzsh_dir"
fi

stow_component "$component_root"
mkdir -p -- "${XDG_STATE_HOME:-$HOME/.local/state}/zsh"

zsh -n "$component_root/dotfiles/.zshenv"
zsh -n "$component_root/dotfiles/.zshrc"
zsh -n "$component_root/dotfiles/.config/zsh/aliases.zsh"
zsh -n "$component_root/dotfiles/.config/zsh/functions.zsh"

zsh_path=$(command -v zsh)
current_shell=$(getent passwd "$(id -un)" | cut -d: -f7)
if [[ $(realpath -m -- "$current_shell") != $(realpath -m -- "$zsh_path") ]]; then
    printf 'Changing the default shell from %s to %s\n' "$current_shell" "$zsh_path"
    if ! sudo usermod --shell "$zsh_path" "$(id -un)"; then
        printf 'Could not change the login shell with usermod; trying chsh.\n' >&2
        if ! chsh -s "$zsh_path"; then
            printf 'Run manually: chsh -s %s\n' "$zsh_path" >&2
        fi
    fi
fi

printf 'Zsh shell environment installed. Open a new terminal to use it.\n'
