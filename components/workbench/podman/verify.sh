#!/usr/bin/env bash
set -euo pipefail
profile=$1
[[ $HOME != /host-home && -d /host-home && -w $HOME ]]
[[ $XDG_CONFIG_HOME == "$HOME/.config" && $XDG_DATA_HOME == "$HOME/.local/share" ]]
# Inspect the new home only. Do not write a test file to the real/shared home.
for path in "$HOME/.zshrc" "$HOME/.zshenv" "$HOME/.config/nvim" "$HOME/.config/nvim/init.lua"; do
    [[ ! -L $path ]]
    [[ -e $path ]]
done
for tool in nvim zsh starship fastfetch eza bat fd fzf rg zoxide git lazygit node npm python yazi; do
    command -v "$tool"
done
DOTFILES_FASTFETCH=0 zsh -lic 'exit'
nvim --headless +qa
if [[ $profile == dev ]]; then
    zsh -lc 'command -v flutter; command -v adb; command -v dotnet; command -v rider; command -v dbeaver; command -v hermes'
    zsh -lc 'flutter --version; "$ANDROID_HOME/emulator/emulator" -list-avds; dotnet --list-sdks'
else
    [[ ! -e $HOME/.local/share/flutter-dev && ! -e $HOME/.config/flutter ]]
    [[ ! -e /opt/hermes && ! -e /opt/rider ]]
fi
printf 'Verificado: %s; home interno %s; archivos compartidos /host-home.\n' "$profile" "$HOME"
