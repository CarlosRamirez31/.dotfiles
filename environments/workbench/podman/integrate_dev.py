#!/usr/bin/env python3
"""Configure only the new dev's private home and presentation desktop."""
import os
from pathlib import Path
import shutil
import subprocess

def configure(home, host, root):
    endpoint = 'unix:///host-home/.local/state/podman-workbench/docker.sock'
    helper = home / '.local/libexec/dotfiles-container-env'
    if helper.exists():
        text = helper.read_text()
        original = 'socket="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/podman/podman.sock"'
        helper.write_text(text.replace(original, 'socket="/host-home/.local/state/podman-workbench/docker.sock"'))
    for name in ('.zshenv', '.bashrc'):
        file = home / name
        text = file.read_text() if file.exists() else ''
        marker = '# Podman workbench host connection'
        if marker not in text:
            file.write_text(text + '\n' + marker + '\n'
                            'if [ -z "${DOCKER_HOST:-}" ] && [ -z "${DOCKER_CONTEXT:-}" ]; then\n'
                            f'    export DOCKER_HOST="{endpoint}"\nfi\n'
                            'export XCURSOR_THEME=Bibata-Modern-Classic XCURSOR_SIZE=24\n')
    # Share only the existing wallpaper collection, keeping selection state private.
    wallpapers = home / 'Pictures/Wallpapers'
    wallpapers.parent.mkdir(parents=True, exist_ok=True)
    if not wallpapers.exists() and not wallpapers.is_symlink():
        wallpapers.symlink_to(host / 'Pictures/Wallpapers', target_is_directory=True)
    current = host / '.local/state/dotfiles/wallpaper'
    saved = current.read_text().strip() if current.exists() else ''
    original_home = str(home)
    if saved.startswith(original_home + '/'):
        saved = '/host-home/' + saved[len(original_home) + 1:]
    if saved and Path(saved).is_file() and (root / "config").is_dir():
        (root / 'config/wallpaper-path').write_text(saved + '\n')
        state = home / '.local/state/dotfiles/wallpaper'
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(saved + '\n')
    # Theme files are installed in the private home, including presentation's XDG tree.
    icons = home / '.icons'
    icons.mkdir(exist_ok=True)
    for theme in ('Bibata-Modern-Classic', 'Oranchelo'):
        source = Path('/host-home/.local/share/icons') / theme
        if not source.is_dir():
            source = Path('/tmp/workbench-icons') / theme
        if source.is_dir():
            destination = icons / theme
            destination.mkdir(exist_ok=True)
            subprocess.run(['cp', '-a', str(source) + '/.', str(destination)], check=True)
    default = icons / 'default'
    default.mkdir(exist_ok=True)
    (default / 'index.theme').write_text('[Icon Theme]\nInherits=Bibata-Modern-Classic\n')
    resources = home / '.Xresources'
    resources.write_text('Xcursor.theme: Bibata-Modern-Classic\nXcursor.size: 24\n')
    for base in ([home / '.config'] + [root / 'xdg/config'] if root.is_dir() else [home / '.config']):
        for gtk in ('gtk-3.0', 'gtk-4.0'):
            settings = base / gtk / 'settings.ini'
            settings.parent.mkdir(parents=True, exist_ok=True)
            source = host / '.config' / gtk / 'settings.ini'
            if source.is_file():
                shutil.copyfile(source, settings)
    desktop = root / 'bin/desktop-session'
    text = desktop.read_text() if desktop.is_file() else ""
    marker = '# Workbench cursor'
    if desktop.is_file() and marker not in text:
        text = text.replace('exec awesome', marker + '\n'
                            'export XCURSOR_THEME=Bibata-Modern-Classic XCURSOR_SIZE=24\n'
                            'xrdb -merge "$HOME/.Xresources"\n'
                            'xsetroot -cursor_name left_ptr\nexec awesome')
        desktop.write_text(text)
    print('Docker conectado y apariencia del host aplicada al dev nuevo.')


if __name__ == '__main__':
    if os.environ.get('PODMAN_WORKBENCH') != 'dev-podman':
        raise SystemExit('Solo se permite dev-podman.')
    configure(Path.home(), Path('/host-home'), Path('/opt/presentacion'))
