#!/usr/bin/env python3
"""Adapt only the NEW dev's presentation to Podman and its private PID namespace."""
import os
from pathlib import Path

def adapt(root):
    if os.environ.get('PODMAN_WORKBENCH') != 'dev-podman':
        raise SystemExit('Esta adaptación solo se ejecuta en dev-podman.')
    if not root.is_dir():
        raise SystemExit('Falta /opt/presentacion en el contenedor nuevo.')
    fonts = root / 'config/fonts.conf'
    if fonts.exists():
        fonts.write_text(fonts.read_text().replace('/run/host/usr/share/fonts', '/usr/share/fonts'))
    name = os.environ['PODMAN_WORKBENCH']
    uidgid = f'{os.getuid()}:{os.getgid()}'
    script = root / 'bin/presentacion.py'
    text = script.read_text()
    text = text.replace('Distrobox dev', 'dev-podman')
    text = text.replace("'Presentación · dev'", "'Presentación · dev-podman'")
    text = text.replace("['xdotool','search','--class','^Xephyr$']",
                        "['xdotool','search','--name','^Presentación · dev-podman$']")
    text = text.replace("['distrobox-host-exec','alacritty','--title','HERMES_PRIVADO','-e','distrobox','enter','dev']",
                        "['alacritty','--title','HERMES_PRIVADO','-e','zsh','-l']")
    if 'distrobox-host-exec' in text:
        raise SystemExit('Queda un lanzador de host sin adaptar en presentación.')
    script.write_text(text)

    keys = root / 'bin/host_hotkeys.py'
    text = keys.read_text()
    text = text.replace("{'distrobox','enter','dev','--','/opt/presentacion/bin/screenshot'",
                        "{'podman','exec','--user','" + uidgid + "','" + name + "','/opt/presentacion/bin/screenshot'")
    start = text.find('local function alive()')
    if start != -1:
        end = text.index('return true\n\'\'\'', start)
        replacement = """local checking=false;
    rec.timer=gears.timer({timeout=2,autostart=true,callback=function()
     if checking then return end;checking=true;
     awful.spawn.easy_async({'podman','exec','--user','UIDGID','CONTAINER','python3','/opt/presentacion/bin/bridge-alive.py','PID','START'},
     function(stdout,stderr,reason,code) checking=false;if code~=0 then rec.restore() end end)
    end});
    """.replace('UIDGID', uidgid).replace('CONTAINER', name)
        text = text[:start] + replacement + text[end:]
    if "'distrobox','enter'" in text:
        raise SystemExit('Quedan atajos que apuntan al Distrobox original.')
    keys.write_text(text)

    alive = root / 'bin/bridge-alive.py'
    alive.write_text('''#!/usr/bin/env python3
    import pathlib, sys
    try:
        pid=int(sys.argv[1])
        data=pathlib.Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        raise SystemExit(0 if data[19] == sys.argv[2] and data[0] != 'Z' else 1)
    except (OSError,ValueError,IndexError):
        raise SystemExit(1)
    '''.replace('\n    ', '\n'))
    alive.chmod(0o755)
    for file in (script, keys, alive):
        compile(file.read_text(), str(file), 'exec')
    print('Presentación adaptada al nuevo Podman; Distrobox original intacto.')


if __name__ == '__main__':
    adapt(Path('/opt/presentacion'))
