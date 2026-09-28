# Desktop extras

Agrupa aplicaciones útiles que no son necesarias para arrancar Hyprland, permitiendo omitir navegador, gestor de contraseñas y utilidades en una instalación mínima.

## Programas incluidos

| Paquete/comando | Uso |
| --- | --- |
| `firefox` | Navegador predeterminado HTTP/HTTPS/HTML. |
| `keepassxc` | Bóveda local; no crea ni sincroniza bases automáticamente. |
| `btop` | CPU, memoria, red, discos y procesos. |
| `wf-recorder` | Grabación nativa de Wayland. |
| `hyprpicker` | Selector de color y copia al portapapeles. |
| `trash-cli` | Papelera Freedesktop recuperable desde terminal. |

## Atajos y comandos

```bash
./install.sh desktop-extras
btop
keepassxc
trash-put archivo
trash-list
trash-restore
trash-empty
```

| Atajo | Acción |
| --- | --- |
| `Alt+B` | Firefox dentro de UWSM. |
| `Alt+Shift+R` | Seleccionar región e iniciar/detener grabación. |
| `Alt+Shift+C` | Elegir y copiar color. |

`dotfiles-record area` usa Slurp; `dotfiles-record full` graba la salida completa. Guarda MP4 con fecha/hora en `$(xdg-user-dir VIDEOS)/Recordings`, mantiene PID y log en `$XDG_RUNTIME_DIR` y envía `SIGINT` para cerrar correctamente el vídeo.

```bash
dotfiles-record area
dotfiles-record full
tail -f "$XDG_RUNTIME_DIR/dotfiles-wf-recorder.log"
```

El archivo administrado es `.local/bin/dotfiles-record`. Los atajos vienen de `hyprland`, Slurp/notificaciones de otros componentes y las asociaciones Firefox de `files`. No se reemplaza `rm`: la papelera es explícita.

## Diagnóstico

```bash
command -v firefox keepassxc btop wf-recorder hyprpicker trash-put
pgrep -a wf-recorder
echo "$WAYLAND_DISPLAY"
```

Una grabación negra suele indicar que no se ejecuta dentro de la sesión Wayland. No se puede capturar desde una TTY o una sesión SSH sin acceso al compositor.
