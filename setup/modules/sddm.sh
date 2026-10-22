#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../lib.sh"

theme_source="$DOTFILES_ROOT/system/sddm/theme"
theme_target=/usr/share/sddm/themes/silent
font_target=/usr/share/fonts/silent-sddm
config_source="$DOTFILES_ROOT/system/sddm/silent.conf"

require_arch_user
install_packages qt6-svg qt6-virtualkeyboard qt6-multimedia-ffmpeg qt6-imageformats

if [[ ! -f $theme_source/Main.qml || ! -f $theme_source/metadata.desktop || ! -d $theme_source/fonts ]]; then
    printf 'The bundled SilentSDDM theme does not contain the expected files.\n' >&2
    exit 1
fi

sudo rm -rf -- "$theme_target" "$font_target"
sudo install -d -m 0755 "$theme_target" "$font_target" /etc/sddm.conf.d
sudo cp -a "$theme_source"/. "$theme_target"/
sudo cp -a "$theme_target/fonts"/. "$font_target"/
sudo fc-cache -f "$font_target"
sudo install -m 0644 "$config_source" /etc/sddm.conf.d/10-silent.conf

printf 'SilentSDDM is installed. Test it with: sddm-greeter-qt6 --test-mode --theme %s\n' "$theme_target"
