# Desktop extras

Agrupa aplicaciones de uso diario que no son necesarias para iniciar Awesome:
Firefox, Limusic, KeePassXC, Btop, selección de color y papelera.

## Programas incluidos

| Paquete/comando | Uso |
| --- | --- |
| `firefox` | Navegador predeterminado HTTP/HTTPS/HTML. |
| `limusic-bin` (AUR), `limusic-app` | Reproductor de música con Mini Player nativo. |
| `keepassxc` | Bóveda local; no crea ni sincroniza bases automáticamente. |
| `btop` | CPU, memoria, red, discos y procesos. |
| `gpick` | Selector de color X11. |
| `trash-cli` | Papelera recuperable desde terminal. |

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
| `Alt+B` | Firefox. |
| `Alt+Shift+C` | Selector de color. |

## Diagnóstico

```bash
command -v firefox keepassxc btop gpick trash-put
echo "$XDG_SESSION_TYPE"
```

La sesión debe indicar `x11`.

`limusic-bin` se instala mediante el ayudante AUR configurado, también al ejecutar
la instalación completa por primera vez. Si ya está instalado se conserva.
El botón de música de Polybar abre un panel ligero de Awesome que controla el
reproductor activo por MPRIS, incluido Limusic. No abre el Mini Player de la
aplicación ni una segunda instancia.

## Fuentes del módulo

Instalador: [`setup/modules/desktop-extras.sh`](../setup/modules/desktop-extras.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
