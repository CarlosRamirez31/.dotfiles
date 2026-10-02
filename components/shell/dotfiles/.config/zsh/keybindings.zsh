# Text editing that follows the conventions used by graphical applications.
# Alacritty sends the corresponding CSI sequences explicitly.
_dotfiles_start_selection() {
    if (( ! REGION_ACTIVE )); then
        MARK=$CURSOR
        REGION_ACTIVE=1
    fi
}

_dotfiles_select_backward_char() {
    _dotfiles_start_selection
    zle backward-char
}

_dotfiles_select_forward_char() {
    _dotfiles_start_selection
    zle forward-char
}

_dotfiles_select_backward_word() {
    _dotfiles_start_selection
    zle backward-word
}

_dotfiles_select_forward_word() {
    _dotfiles_start_selection
    zle forward-word
}

zle -N dotfiles-select-backward-char _dotfiles_select_backward_char
zle -N dotfiles-select-forward-char _dotfiles_select_forward_char
zle -N dotfiles-select-backward-word _dotfiles_select_backward_word
zle -N dotfiles-select-forward-word _dotfiles_select_forward_word

for keymap in emacs viins; do
    # Alacritty translates Ctrl+Backspace to Ctrl+W. Keep Ctrl+W itself useful
    # as the conventional terminal shortcut for deleting the previous word.
    bindkey -M "$keymap" '^W' backward-kill-word
    bindkey -M "$keymap" '^[[1;2D' dotfiles-select-backward-char
    bindkey -M "$keymap" '^[[1;2C' dotfiles-select-forward-char
    bindkey -M "$keymap" '^[[1;6D' dotfiles-select-backward-word
    bindkey -M "$keymap" '^[[1;6C' dotfiles-select-forward-word
done
unset keymap
