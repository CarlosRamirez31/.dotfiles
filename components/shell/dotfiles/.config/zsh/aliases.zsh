# Navigation and readable directory listings.
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ls='eza --icons=always --group-directories-first'
alias l='eza --icons=always --group-directories-first'
alias la='eza -a --icons=always --group-directories-first'
alias ll='eza -lah --icons=always --group-directories-first --git --time-style=long-iso'
alias lt='eza --tree --level=2 --icons=always --group-directories-first'
alias tree='eza --tree --icons=always --group-directories-first'

# Better defaults for reading and searching files.
alias cat='bat --paging=never --style=plain'
alias catp='/usr/bin/cat'
alias less='less -R'
alias grep='grep --color=auto'
alias rg='rg --smart-case'

# Development shortcuts.
alias nv='nvim'
alias lg='lazygit'
alias py='python'
alias reload='exec zsh'
alias sysinfo='fastfetch'
alias pathlist='print -l $path'
if (( $+commands[pacman] )); then
    alias update='sudo pacman -Syu'
    alias pacsearch='pacman -Ss'
    alias pacinfo='pacman -Si'
elif (( $+commands[apt] )); then
    alias update='sudo apt update && sudo apt full-upgrade'
    alias pacsearch='apt search'
    alias pacinfo='apt show'
fi

# Networking and authorized assessment helpers.
alias ipa='ip -brief -color address'
alias routes='ip -color route'
alias sockets='ss -tulpen'
alias dnsinfo='resolvectl status'
alias nmap-basic='nmap -sC -sV'
alias nmap-full='nmap -p- --min-rate 1000'
alias httpheaders='curl -I'

# Friendly entry points for user-facing dotfiles tools. Their implementation
# keeps the dotfiles-* namespace so desktop services cannot collide with
# system commands, while interactive use stays concise.
alias doctor='dotfiles-doctor'
alias maintain='dotfiles-maintain'
alias backup='dotfiles-backup'
alias lab-firewall='dotfiles-firewall'
alias htb-target='dotfiles-htb-target'
alias record='dotfiles-record'
alias screenshot='dotfiles-screenshot'
alias clip='dotfiles-clipboard'
alias clip-clear='dotfiles-clipboard-clear'
