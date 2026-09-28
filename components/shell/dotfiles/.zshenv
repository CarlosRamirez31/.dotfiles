# Keep portable user tools available in login, interactive, and script shells.
typeset -U path PATH

for user_bin in \
    "$HOME/.local/bin" \
    "$HOME/.cargo/bin" \
    "$HOME/.pub-cache/bin" \
    "$HOME/development/flutter/bin" \
    "$HOME/flutter/bin" \
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
