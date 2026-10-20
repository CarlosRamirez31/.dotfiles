# Keep portable user tools available in login, interactive, and script shells.
typeset -U path PATH

# Installed only by explicit selection of ./install.sh flutter.
if [[ -r ${XDG_CONFIG_HOME:-$HOME/.config}/flutter/env.zsh ]]; then
    source "${XDG_CONFIG_HOME:-$HOME/.config}/flutter/env.zsh"
fi

for user_bin in \
    "$HOME/.local/bin" \
    "$HOME/.cargo/bin" \
    "$HOME/.pub-cache/bin" \
    "$HOME/development/flutter/bin" \
    "$HOME/flutter/bin" \
    "${FLUTTER_HOME:-$HOME/development/flutter}/bin" \
    "${JAVA_HOME:-/usr/lib/jvm/default}/bin" \
    "${ANDROID_HOME:-$HOME/Android/Sdk}/cmdline-tools/latest/bin" \
    "${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Android/Sdk}}/platform-tools" \
    "${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Android/Sdk}}/emulator"
do
    [[ -d $user_bin ]] && path=("$user_bin" $path)
done

export PATH
export SHELL="${commands[zsh]:-/usr/bin/zsh}"
export EDITOR="${EDITOR:-nvim}"
export VISUAL="${VISUAL:-nvim}"
export PAGER="${PAGER:-less}"
export LESS='-R --mouse'

# GNOME Keyring exposes an SSH agent through the user runtime directory. This
# keeps Git/SSH credentials available to both terminals and graphical tools.
if [[ -n ${XDG_RUNTIME_DIR:-} && -S $XDG_RUNTIME_DIR/gcr/ssh ]]; then
    export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/gcr/ssh"
fi
