# Desktop extras

Agrupa aplicaciones de uso diario que no son necesarias para iniciar Awesome:
Firefox, KeePassXC, Btop, grabación X11, selección de color y papelera.

## Programas incluidos

| Paquete/comando | Uso |
| --- | --- |
| `firefox` | Navegador predeterminado HTTP/HTTPS/HTML. |
| `keepassxc` | Bóveda local; no crea ni sincroniza bases automáticamente. |
| `btop` | CPU, memoria, red, discos y procesos. |
| `ffmpeg` | Grabación de pantalla con `x11grab`. |
| `gpick` | Selector de color X11. |
| `trash-cli` | Papelera recuperable desde terminal. |

## Atajos y comandos

```bash
./install.sh desktop-extras
btop
keepassxc
dotfiles-record area
dotfiles-record full
trash-put archivo
trash-list
trash-restore
trash-empty
```

| Atajo | Acción |
| --- | --- |
| `Alt+B` | Firefox. |
| `Alt+Shift+R` | Iniciar/detener grabación de una región. |
| `Alt+Shift+C` | Selector de color. |

`dotfiles-record area` usa Slop para elegir la región; `full` toma la pantalla
completa mediante XRandR. FFmpeg graba en MP4 dentro de
`$(xdg-user-dir VIDEOS)/Recordings`; `Alt+Shift+R` vuelve a pulsarse para cerrar
el archivo limpiamente.

## Diagnóstico

```bash
command -v firefox keepassxc btop ffmpeg gpick trash-put
pgrep -a ffmpeg
echo "$XDG_SESSION_TYPE"
```

La sesión debe indicar `x11`.

## Fuentes del módulo

Instalador: [`setup/modules/desktop-extras.sh`](../setup/modules/desktop-extras.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
