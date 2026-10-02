#!/usr/bin/env bash
set -euo pipefail

component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$component_root/../../scripts/lib.sh"

require_arch_user
install_aur_packages ags-hyprpanel-git
install_packages jq openvpn
stow_component "$component_root"

runtime_dir="$HOME/.config/hyprpanel"
marker="$runtime_dir/.managed-by-dotfiles"
if [[ (-e $runtime_dir || -L $runtime_dir) && ! -f $marker ]]; then
    backup="${runtime_dir}.backup.$(date +%Y%m%d-%H%M%S)"
    printf 'Backing up %s to %s\n' "$runtime_dir" "$backup"
    mv -- "$runtime_dir" "$backup"
fi

mkdir -p -- "$runtime_dir"

# Monitor one mount point per physical filesystem. MAJ:MIN deduplicates bind
# mounts and subvolumes that report the same capacity, while still including
# separate partitions such as /, /home and /boot plus mounted external disks.
mapfile -t storage_paths < <(
    findmnt --real --raw --noheadings --output MAJ:MIN,TARGET |
        awk '!seen[$1]++ { print $2 }'
)
((${#storage_paths[@]} > 0)) || storage_paths=(/)
storage_paths_json=$(jq -n --args '$ARGS.positional' "${storage_paths[@]}")
config_tmp=$(mktemp "$runtime_dir/config.json.XXXXXX")
jq --argjson paths "$storage_paths_json" \
    '.["bar.customModules.storage.paths"] = $paths' \
    "$component_root/templates/config.json" >"$config_tmp"
install -m 0644 -- "$config_tmp" "$runtime_dir/config.json"
rm -- "$config_tmp"
install -m 0644 -- "$component_root/templates/modules.json" "$runtime_dir/modules.json"
install -m 0644 -- "$component_root/templates/modules.scss" "$runtime_dir/modules.scss"
touch -- "$marker"

systemctl --user daemon-reload
systemctl --user enable dotfiles-hyprpanel.service
if [[ -n ${HYPRLAND_INSTANCE_SIGNATURE:-} ]]; then
    systemctl --user stop waybar.service >/dev/null 2>&1 || true
    pkill -x waybar >/dev/null 2>&1 || true
    systemctl --user stop dotfiles-hyprpanel.service >/dev/null 2>&1 || true
    pkill -x hyprpanel >/dev/null 2>&1 || true
    systemctl --user start dotfiles-hyprpanel.service
fi

printf 'HyprPanel installed and configured.\n'
