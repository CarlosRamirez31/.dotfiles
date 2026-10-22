# Oh My Zsh lives outside this repository so the dotfiles keep a single Git
# history. The component installer clones or updates it here.
export ZSH="${XDG_DATA_HOME:-$HOME/.local/share}/oh-my-zsh"
ZSH_THEME=""
zstyle ':omz:update' mode disabled

plugins=(
    git
    sudo
    colored-man-pages
    copypath
    copyfile
    dirhistory
    extract
    history
)

if [[ -r $ZSH/oh-my-zsh.sh ]]; then
    source "$ZSH/oh-my-zsh.sh"
else
    autoload -Uz compinit
    compinit
fi

# Large persistent history. Prefix a sensitive command with one space to keep
# it out of the history file.
ZSH_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}/zsh"
mkdir -p -- "$ZSH_STATE_HOME"
HISTFILE="$ZSH_STATE_HOME/history"
HISTSIZE=100000
SAVEHIST=100000
setopt EXTENDED_HISTORY
setopt SHARE_HISTORY
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_IGNORE_SPACE
setopt HIST_REDUCE_BLANKS
setopt HIST_SAVE_BY_COPY

setopt AUTO_CD
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS
setopt PUSHD_SILENT
setopt INTERACTIVE_COMMENTS

export EZA_ICONS_AUTO=1
export BAT_THEME='TwoDark'
if (( $+commands[vivid] )); then
    export LS_COLORS="$(vivid generate tokyonight-night)"
fi

# Rich, case-insensitive completion menus.
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "$ZSH_STATE_HOME/completion-cache"

export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND='fd --hidden --follow --exclude .git'
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'
export FZF_DEFAULT_OPTS='--height=70% --layout=reverse --border=rounded --info=inline --prompt="  " --pointer="❯" --marker="✓" --color=bg+:#292e42,bg:#1a1b26,spinner:#bb9af7,hl:#7aa2f7,fg:#c0caf5,header:#7dcfff,info:#9ece6a,pointer:#f7768e,marker:#e0af68,fg+:#c0caf5,prompt:#bb9af7,hl+:#7dcfff,border:#3b4261'
export FZF_CTRL_T_OPTS="--preview 'bat --color=always --style=numbers --line-range=:300 {} 2>/dev/null || eza --tree --level=2 --icons=always {}'"
export FZF_ALT_C_OPTS="--preview 'eza --tree --level=2 --icons=always --color=always {}'"

if (( $+commands[fzf] )) && [[ -t 0 && -t 1 ]]; then
    source <(fzf --zsh)
fi

if (( $+commands[zoxide] )); then
    eval "$(zoxide init zsh)"
fi

source "${XDG_CONFIG_HOME:-$HOME/.config}/zsh/aliases.zsh"
source "${XDG_CONFIG_HOME:-$HOME/.config}/zsh/functions.zsh"
source "${XDG_CONFIG_HOME:-$HOME/.config}/zsh/keybindings.zsh"

zsh_autosuggestions=''
for plugin_file in \
    /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh \
    /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
do
    if [[ -r $plugin_file ]]; then
        zsh_autosuggestions=$plugin_file
        break
    fi
done
if [[ -n $zsh_autosuggestions ]]; then
    ZSH_AUTOSUGGEST_STRATEGY=(history completion)
    ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#565f89'
    source "$zsh_autosuggestions"
fi

if [[ -r /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh ]]; then
    source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh
    bindkey '^[[A' history-substring-search-up
    bindkey '^[[B' history-substring-search-down
fi

if (( $+commands[starship] )) && [[ ${TERM:-dumb} != dumb ]]; then
    eval "$(starship init zsh)"
fi

# Show the system card when a new interactive terminal opens. Set
# DOTFILES_FASTFETCH=0 before starting Zsh if you prefer to disable it.
if (( $+commands[fastfetch] )) && [[ -o interactive && -t 1 && ${DOTFILES_FASTFETCH:-1} == 1 ]]; then
    fastfetch
fi

# Syntax highlighting must remain the final sourced plugin.
zsh_syntax_highlighting=''
for plugin_file in \
    /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh \
    /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
do
    if [[ -r $plugin_file ]]; then
        zsh_syntax_highlighting=$plugin_file
        break
    fi
done
if [[ -n $zsh_syntax_highlighting ]]; then
    source "$zsh_syntax_highlighting"
fi
