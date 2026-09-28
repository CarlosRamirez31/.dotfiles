# Navigation and readable directory listings.
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias l='eza --icons=auto --group-directories-first'
alias la='eza -a --icons=auto --group-directories-first'
alias ll='eza -lah --icons=auto --group-directories-first --git --time-style=long-iso'
alias lt='eza --tree --level=2 --icons=auto --group-directories-first'
alias tree='eza --tree --icons=auto --group-directories-first'

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
alias update='sudo pacman -Syu'
alias pacsearch='pacman -Ss'
alias pacinfo='pacman -Si'

# Networking and authorized assessment helpers.
alias ipa='ip -brief -color address'
alias routes='ip -color route'
alias sockets='ss -tulpen'
alias dnsinfo='resolvectl status'
alias nmap-basic='nmap -sC -sV'
alias nmap-full='nmap -p- --min-rate 1000'
alias httpheaders='curl -I'
