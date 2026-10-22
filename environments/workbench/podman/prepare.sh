#!/usr/bin/env bash
# Only run through podman exec --user 0 in a NEW, independently named container.
set -euo pipefail
uid=$1 gid=$2 username=$3 user_home=$4 install_packages=$5
shift 5
[[ $uid != 0 && $user_home == /home/* && $user_home != /host-home* ]]
source /etc/os-release
# A snapshot retains Distrobox's package-manager hooks. Mask them only in this
# new root so future package installations cannot restore host integration.
if command -v pacman >/dev/null; then
    install -d /etc/pacman.d/hooks
    for hook in /usr/share/libalpm/hooks/*distrobox* /etc/pacman.d/hooks/*distrobox*; do
        [[ -e $hook || -L $hook ]] || continue
        ln -sfn /dev/null "/etc/pacman.d/hooks/${hook##*/}"
    done
fi
if [[ $install_packages == yes ]]; then
    if command -v pacman >/dev/null; then
        pacman -Syu --needed --noconfirm sudo bash tar gzip "$@"
    elif command -v apt-get >/dev/null; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y --no-install-recommends sudo bash tar gzip ca-certificates "$@"
        if apt-cache policy yazi | awk '/Candidate:/ { ok = ($2 != "(none)") } END { exit !ok }'; then
            apt-get install -y --no-install-recommends yazi
        else
            printf 'Yazi no está disponible en los repositorios de esta imagen.\n' >&2
        fi
    else
        printf 'Distribución no compatible: %s\n' "$ID" >&2
        exit 1
    fi
fi
if [[ $install_packages == no ]] && command -v pacman >/dev/null; then
    pacman -S --needed --noconfirm luarocks lua51 rust-analyzer \
        ttf-jetbrains-mono-nerd ttf-iosevka-nerd ttf-material-icons noto-fonts-emoji \
        xorg-xrdb xorg-xsetroot
fi
if ! getent group "$gid" >/dev/null; then
    groupadd --gid "$gid" "$username"
fi
if getent passwd "$username" >/dev/null; then
    [[ $(id -u "$username") == "$uid" ]]
elif getent passwd "$uid" >/dev/null; then
    existing=$(getent passwd "$uid" | cut -d: -f1)
    usermod --login "$username" "$existing"
else
    useradd --uid "$uid" --gid "$gid" --home-dir "$user_home" --shell /bin/zsh "$username"
fi
usermod --home "$user_home" --shell /bin/zsh "$username"
[[ ! -L $user_home ]]
install -d -m 700 -o "$uid" -g "$gid" "$user_home" "/run/user/$uid"
install -d -m 700 -o "$uid" -g "$gid" "$user_home/.config" "$user_home/.local" "$user_home/.local/bin" "$user_home/.local/share" "$user_home/.local/libexec" "$user_home/.cache" "$user_home/.local/state"
printf '%s ALL=(ALL) NOPASSWD: ALL\n' "$username" >/etc/sudoers.d/podman-workbench
chmod 440 /etc/sudoers.d/podman-workbench
visudo -cf /etc/sudoers.d/podman-workbench
install -d -m 755 /usr/local/bin
if [[ -d /host-x11 ]]; then
    install -d -m 1777 /tmp/.X11-unix
    for socket in /host-x11/X*; do
        [[ -S $socket ]] || continue
        ln -sfn -- "$socket" "/tmp/.X11-unix/${socket##*/}"
    done
fi
# Remove only integration inherited by the NEW snapshot, never in the source.
for file in /etc/profile.d/distrobox_profile.sh /etc/profile.d/distrobox.sh; do
    if [[ -e $file ]]; then mv -- "$file" "$file.disabled"; fi
done
for pair in fd:fdfind bat:batcat; do
    name=${pair%:*} target=${pair#*:}
    if ! command -v "$name" >/dev/null && command -v "$target" >/dev/null; then
        ln -s -- "$(command -v "$target")" "/usr/local/bin/$name"
    fi
done
if [[ -L /usr/local/bin/xdg-open ]] && [[ $(readlink /usr/local/bin/xdg-open) == *distrobox* ]]; then
    rm -- /usr/local/bin/xdg-open
fi
