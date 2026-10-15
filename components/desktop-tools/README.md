# Desktop tools

Implementa capturas e historial del portapapeles para X11. Maim captura, Slop
selecciona regiones, Flameshot permite anotar, Xclip integra el portapapeles y
Clipmenu guarda el historial que Rofi presenta bajo demanda.

## Dependencias

| Paquete | Función |
| --- | --- |
| `maim` | Captura completa o de una región X11. |
| `slop` | Selecciona la región para captura y grabación. |
| `xclip` | Copia imágenes y texto al portapapeles X11. |
| `clipmenu` | Historial del portapapeles con `clipmenud` y Rofi. |
| `flameshot` | Captura interactiva y anotación. |

## Capturas

```bash
./install.sh desktop-tools
dotfiles-screenshot full
dotfiles-screenshot area
dotfiles-screenshot edit
```

Las imágenes se guardan con fecha y hora en `$(xdg-user-dir PICTURES)/Screenshots`
y se copian al portapapeles. `edit` abre Flameshot en modo X11.

| Atajo | Acción |
| --- | --- |
| `Print` | Pantalla completa. |
| `Alt+Print` | Seleccionar región. |
| `Alt+Shift+S` | Capturar región y anotar. |

## Portapapeles

```bash
dotfiles-clipboard
dotfiles-clipboard-clear
```

`Alt+C` abre el historial en Rofi. Elegir una entrada la copia al portapapeles;
la aplicación receptora puede pegarla con su atajo habitual. `clipmenud` observa
el portapapeles X11 durante la sesión Awesome. La limpieza exige confirmar en
Rofi.

## Diagnóstico

```bash
command -v maim slop xclip clipmenu clipmenud flameshot
pgrep -a -u "$USER" -f '[c]lipmenud'
journalctl --user -b | rg -i 'clipmenu|flameshot|maim'
```

Este componente no inicia servicios Wayland ni depende de Grim, Slurp,
wl-clipboard o Cliphist.
