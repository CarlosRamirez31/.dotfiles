#!/usr/bin/env bash
set -euo pipefail
[[ ${CONTAINER_ID:-} == dev ]] || {
    printf 'Ejecuta este instalador dentro de dev.\n' >&2
    exit 1
}
component_root=${1:?Falta la ruta del repositorio}/environments/hermes
python - <<'PY'
from pathlib import Path
import json
p=Path('/opt/presentacion/run/state.json')
if p.exists():
    state=json.loads(p.read_text())
    try: active=b'presentacion.py' in Path(f"/proc/{int(state['pid'])}/cmdline").read_bytes()
    except OSError: active=False
    if active: raise SystemExit('Cierra primero la sesión con presentacion cerrar y vuelve a instalar. No se ha cambiado nada.')
PY
sudo -v
sudo install -d -m 755 -o "$(id -un)" -g "$(id -gn)" /opt/presentacion /opt/hermes
package_before=$(mktemp /opt/presentacion/.packages-before.XXXXXX)
trap 'rm -f -- "$package_before"' EXIT
pacman -Qq >"$package_before"
sudo pacman -Syu --needed --noconfirm base-devel git curl python python-pip python-yaml \
    xorg-server-xephyr xorg-xdpyinfo xorg-xrandr xorg-xauth xorg-setxkbmap \
    xdotool scrot xclip awesome polybar rofi alacritty feh picom firefox yazi \
    dbus libpulse ttf-dejavu zsh starship fastfetch eza bat fd fzf ripgrep zoxide vivid \
    zsh-autosuggestions zsh-syntax-highlighting zsh-completions zsh-history-substring-search
python "$component_root/configure.py" --component "$component_root" --packages-before "$package_before"
export HERMES_HOME=/opt/hermes/.hermes
export HERMES_RUNTIME_DIR=/opt/hermes/.hermes/tools
export XDG_CACHE_HOME=/opt/hermes/cache
export UV_CACHE_DIR=/opt/hermes/cache/uv
export UV_PYTHON_INSTALL_DIR=/opt/hermes/tools/python
export UV_TOOL_DIR=/opt/hermes/tools/uv
mkdir -p /opt/hermes/.local/bin
if [[ ! -x /opt/hermes/.hermes/hermes-agent/.hermes/bin/hermes ]]; then
    curl --fail --silent --show-error --location --proto '=https' \
        https://raw.githubusercontent.com/NousResearch/hermes-agent/d923a5eb487a17c0a68801bba9ef0f56c81040a8/scripts/install.sh -o /opt/hermes/install.sh
    # Run only the headless stages. The upstream products stage also writes
    # ~/.local/bin and shell startup files, which must remain private to this installation.
    # Keep those untouched; publish only an internal launcher below instead.
    for stage in prerequisites repository venv python-deps config; do
        bash /opt/hermes/install.sh --non-interactive --skip-browser --skip-computer-use \
            --dir /opt/hermes/.hermes/hermes-agent \
            --commit d923a5eb487a17c0a68801bba9ef0f56c81040a8 --stage "$stage"
    done
    python /opt/hermes/.hermes/hermes-agent/hermes_cli/_launchers.py \
        /opt/hermes/.hermes/hermes-agent/.hermes/bin
    bash /opt/hermes/install.sh --non-interactive --skip-browser --skip-computer-use \
        --dir /opt/hermes/.hermes/hermes-agent \
        --commit d923a5eb487a17c0a68801bba9ef0f56c81040a8 --stage complete
fi
sudo install -m 755 "$component_root/wrappers/hermes" /usr/local/bin/hermes
sudo install -m 755 "$component_root/wrappers/presentacion" /usr/local/bin/presentacion
if [[ ! -x /opt/hermes/.hermes/academic/.venv/bin/python ]]; then
    python -m venv /opt/hermes/.hermes/academic/.venv
fi
/opt/hermes/.hermes/academic/.venv/bin/python -m pip install --disable-pip-version-check \
    -r "$component_root/requirements-academic.txt"
hermes --version
printf '\nHermes opcional instalado solo en dev.\n'
printf 'Autenticación (no versionada): dev-podman exec -- hermes setup\n'
printf 'Uso dentro de dev: presentacion iniciar; presentacion hermes\n'
