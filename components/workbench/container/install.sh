#!/usr/bin/env bash
set -euo pipefail

profile=${1:-}
case $profile in
    kali | parrot) ;;
    *)
        printf 'Unsupported lab profile: %s\n' "${profile:-<empty>}" >&2
        exit 2
        ;;
esac

export DEBIAN_FRONTEND=noninteractive

common_packages=(
    bat
    build-essential
    ca-certificates
    cmake
    curl
    dnsutils
    eza
    fastfetch
    fd-find
    file
    fzf
    git
    iproute2
    iputils-ping
    jq
    lazygit
    less
    locales
    neovim
    netcat-openbsd
    nodejs
    npm
    procps
    python3
    python3-pip
    python3-venv
    ripgrep
    socat
    starship
    sudo
    traceroute
    tree-sitter-cli
    unzip
    vivid
    wget
    whois
    wl-clipboard
    zip
    zoxide
    zsh
    zsh-autosuggestions
    zsh-syntax-highlighting
)

kali_packages=(
    enum4linux-ng
    exploitdb
    feroxbuster
    ffuf
    gobuster
    hashcat
    hydra
    john
    metasploit-framework
    nikto
    nmap
    seclists
    smbclient
    sqlmap
    tcpdump
    whatweb
    wordlists
)

apt-get update
apt-get install --yes --no-install-recommends "${common_packages[@]}"
if [[ $profile == kali ]]; then
    apt-get install --yes --no-install-recommends "${kali_packages[@]}"
fi

# Debian-family distributions expose these tools under different names.
ln -sfn /usr/bin/fdfind /usr/local/bin/fd
ln -sfn /usr/bin/batcat /usr/local/bin/bat

git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git /root/.local/share/oh-my-zsh
chsh --shell /usr/bin/zsh root

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
