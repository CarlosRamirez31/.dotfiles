# Some distributions reset PATH in /etc/profile after reading .zshenv.
# Restore portable tools and SDK paths for login shells, including zsh -lc.
if [[ -r $HOME/.zshenv ]]; then
    source "$HOME/.zshenv"
fi
