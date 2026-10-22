#!/usr/bin/env bash
set -euo pipefail
component=${1:?Falta el nombre del componente}
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd -P)
source "$repo_root/setup/lib.sh"
case $component in hermes | flutter | rider | docker | dbeaver) ;; *) exit 2 ;; esac
require_arch_user
controller=$repo_root/bin/dotfiles-podman
case $repo_root in
    "$HOME"/*) internal_root="/host-home/${repo_root#"$HOME"/}" ;;
    *)
        printf 'El repositorio debe estar dentro del home compartido.\n' >&2
        exit 1
        ;;
esac
# The controller requires the existing dev and never installs host packages.
# The home is private: host links alone do not update container launchers or env.
"$controller" exec dev -- python3 "$internal_root/setup/copy-component.py" workbench "$component"
flutter_settings=("FLUTTER_AVD_KEYBOARD=${FLUTTER_AVD_KEYBOARD:-yes}")
for variable in FLUTTER_DEV_HOME ANDROID_AVD_HOME FLUTTER_AVD_NAME; do
    if [[ -v $variable ]]; then flutter_settings+=("$variable=${!variable}"); fi
done
"$controller" exec dev -- env "${flutter_settings[@]}" \
    bash "$internal_root/setup/modules/$component/setup-container.sh" "$internal_root"
if [[ $component == hermes ]]; then
    "$controller" exec dev -- python3 "$internal_root/environments/workbench/podman/adapt_presentation.py"
fi
link_component workbench
link_component "$component"
"$controller" integrate dev
printf '%s disponible en dev-podman.\n' "$component"
