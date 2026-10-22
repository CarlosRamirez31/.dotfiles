# Doctor

`dotfiles-doctor` es la comprobación integral y de solo lectura del escritorio
Awesome/X11. Distingue un requisito roto de una función opcional pendiente. Su
instalador enlaza el script y lo ejecuta al final del despliegue.

## Uso y resultado

```bash
./install.sh doctor
dotfiles-doctor
dotfiles-doctor >/tmp/doctor.txt
```

- `✓`: requisito presente o estado esperado.
- `!`: función opcional ausente o comprobación en vivo no disponible.
- `✗`: requisito esencial roto.

Sale con código `1` cuando hay errores y `0` cuando la base funciona, aunque
existan advertencias.

## Qué comprueba

1. Awesome, Xorg, Picom, Mesa, terminal, lanzador, capturas, portapapeles,
   grabación, wallpaper y bloqueo.
2. Ejecutables administrados en `~/.local/bin`, configuración de Awesome y
   Picom, y enlaces administrados críticos.
3. JetBrainsMono Nerd Font, Noto Color Emoji y Lexend para la Wibar.
4. Zsh como shell de login, NetworkManager, firewall, timers y sockets de
   credenciales.
5. En una sesión Awesome activa: tipo X11,
   Picom, Xss-lock, una sola instancia de Clipmenu, sintaxis Lua y renderer GL.
6. En VMware, detecta `llvmpipe` como error de aceleración.

## Límites

No instala paquetes ni reinicia servicios. Restic e identidad Git pendientes
son informativos porque requieren decisiones privadas. Desde una TTY o SSH
omite las comprobaciones que necesitan una sesión gráfica activa.

## Diagnóstico complementario

```bash
systemctl --failed
systemctl --user --failed
journalctl --user -b -p warning
glxinfo -B
git status
```

El único archivo administrado es `.local/bin/dotfiles-doctor`; no tiene
paquetes propios porque inspecciona los demás componentes.
