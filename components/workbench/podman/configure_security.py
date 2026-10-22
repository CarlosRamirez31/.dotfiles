#!/usr/bin/env python3
"""Apply personal terminal/file preferences only to Parrot and Kali."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from share_documents import share_documents


def ansi_colors(value):
    """Fastfetch before 2.42 accepts SGR RGB, but not #RRGGBB."""
    if isinstance(value, dict):
        return {key: ansi_colors(item) for key, item in value.items()}
    if isinstance(value, list):
        return [ansi_colors(item) for item in value]
    if isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        return '38;2;' + ';'.join(str(int(value[i:i+2], 16)) for i in (1, 3, 5))
    return value


def configure(home, host, repo, profile, ls_colors=''):
    if profile not in ('parrotos', 'kali'):
        raise ValueError('Solo se configuran parrotos y kali.')
    backup_root = home / '.local/state/podman-workbench/preferences-before-security'

    def write(relative, text):
        target = home / relative
        # Never write through a directory symlink into the shared host home.
        if not target.parent.resolve().is_relative_to(home.resolve()):
            raise RuntimeError(f'La configuración apunta fuera del home interno: {relative}')
        target.parent.mkdir(parents=True, exist_ok=True)
        old = target.read_bytes() if target.is_file() else None
        content = text.encode()
        if old == content and not target.is_symlink():
            return
        if old is not None:
            digest = hashlib.sha256(old).hexdigest()[:12]
            backup = backup_root / (relative + '.' + digest)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                backup.write_bytes(old)
        if target.is_symlink():
            target.unlink()
        target.write_bytes(content)

    # Use the user's existing styles, with versioned defaults for fresh hosts.
    paths = {
        'shell': ['.zshrc', '.zshenv', '.config/starship.toml',
                  '.config/zsh/aliases.zsh', '.config/zsh/functions.zsh',
                  '.config/zsh/keybindings.zsh', '.config/bat/config',
                  '.config/lazygit/config.yml'],
        'files': ['.config/yazi/yazi.toml', '.config/yazi/theme.toml', '.config/yazi/keymap.toml'],
        'awesome': ['.config/gtk-3.0/settings.ini', '.config/gtk-4.0/settings.ini', '.Xresources'],
    }
    for component, entries in paths.items():
        for relative in entries:
            source = host / relative
            if not source.is_file():
                source = repo / 'components' / component / 'dotfiles' / relative
            if not source.is_file():
                continue
            text = source.read_text()
            if relative == '.zshrc':
                # Preserve Tokyo Night even when vivid lacks that built-in theme.
                text = re.sub(r'if \(\( \$\+commands\[vivid\] \)\); then\n.*?\nfi',
                    'if [[ -r ${XDG_CONFIG_HOME:-$HOME/.config}/zsh/workbench-ls-colors ]]; then\n'
                    '    export LS_COLORS="$(< "${XDG_CONFIG_HOME:-$HOME/.config}/zsh/workbench-ls-colors")"\n'
                    'elif (( $+commands[vivid] )); then\n'
                    '    export LS_COLORS="$(vivid generate tokyonight-night 2>/dev/null || vivid generate one-dark 2>/dev/null)"\nfi',
                    text, count=1, flags=re.S)
            elif relative.endswith('/aliases.zsh'):
                # Host service/desktop helpers are intentionally not installed here.
                text = '\n'.join(line for line in text.splitlines()
                    if not re.match(r'alias (ld|doctor|maintain|backup|lab-firewall|htb-target|record|screenshot|clip|clip-clear)=', line)) + '\n'
                if not shutil.which('resolvectl'):
                    text = text.replace("alias dnsinfo='resolvectl status'", "alias dnsinfo='/bin/cat /etc/resolv.conf'")
            elif relative == '.zshenv':
                # Keep all SDK activation out of the security shell.
                text = '''typeset -U path PATH
[[ -d $HOME/.local/bin ]] && path=("$HOME/.local/bin" $path)
export PATH SHELL=/bin/zsh EDITOR=nvim VISUAL=nvim PAGER=less
export LESS='-R --mouse'
export XCURSOR_THEME=Bibata-Modern-Classic XCURSOR_SIZE=24
'''
            write(relative, text)
    if ls_colors:
        write('.config/zsh/workbench-ls-colors', ls_colors.strip() + '\n')
    source = host / '.config/fastfetch/config.jsonc'
    if not source.is_file():
        source = repo / 'components/fastfetch/dotfiles/.config/fastfetch/config.jsonc'
    config = ansi_colors(json.loads(source.read_text()))
    # Let Fastfetch select the correct distribution logo instead of Arch's.
    config['logo'].pop('source', None)
    for item in config.get('modules', []):
        if isinstance(item, dict) and item.get('type') == 'os':
            item['key'] = '  Sistema'
    write('.config/fastfetch/config.jsonc', json.dumps(config, indent=2) + '\n')
    share_documents(home, host / 'Documents')
    wallpapers = home / 'Pictures/Wallpapers'
    if (host / 'Pictures/Wallpapers').is_dir() and not wallpapers.exists() and not wallpapers.is_symlink():
        wallpapers.parent.mkdir(parents=True, exist_ok=True)
        wallpapers.symlink_to(host / 'Pictures/Wallpapers', target_is_directory=True)
    # Optional assets arrive from the host through the controller, without apt.
    for theme in ('Bibata-Modern-Classic', 'Oranchelo'):
        source = Path('/tmp/workbench-icons') / theme
        if source.is_dir():
            destination = home / '.icons' / theme
            if not destination.resolve().is_relative_to(home.resolve()):
                raise RuntimeError('El tema de iconos apunta fuera del home interno.')
            destination.mkdir(parents=True, exist_ok=True)
            subprocess.run(['cp', '-a', str(source) + '/.', str(destination)], check=True)
    write('.icons/default/index.theme', '[Icon Theme]\nInherits=Bibata-Modern-Classic\n')
    print(f'{profile}: colores, terminal, Yazi, cursor y Documents configurados; sin SDKs ni Hermes.')


if __name__ == '__main__':
    profile = os.environ.get('PODMAN_WORKBENCH', '').removesuffix('-podman')
    if profile not in ('parrotos', 'kali') or not Path('/run/.containerenv').exists():
        raise SystemExit('Ejecuta este script dentro de parrotos-podman o kali-podman.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    configure(Path.home(), Path('/host-home'), args.repo, profile,
              os.environ.get('WORKBENCH_LS_COLORS', ''))
