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

`Alt+C` abre el historial en Rofi. Elegir una entrada con Enter la copia al
portapapeles y la pega en la ventana original, usando `Ctrl+Shift+V` en
Alacritty y otras terminales, o `Ctrl+V` en aplicaciones gráficas. Requiere
`xdotool` y `xorg-xprop`. La captura de historial está desactivada al iniciar
Awesome: durante el diagnóstico, pausar `clipmenud` coincidió con una bajada
de consumo de aproximadamente 44 W a 33 W. Copiar y pegar normalmente sigue
funcionando, pero las nuevas copias no se guardan en el historial.

Para activar la captura manualmente durante la sesión, ejecuta `clipmenud`
en una terminal; detenlo con `Ctrl+C` cuando termines. `Alt+C` permite elegir
las entradas ya disponibles. La limpieza exige confirmar en Rofi.

## Diagnóstico

```bash
command -v maim slop xclip clipmenu clipmenud flameshot
pgrep -a -u "$USER" -f '[c]lipmenud'
journalctl --user -b | rg -i 'clipmenu|flameshot|maim'
```

Todos sus procesos y dependencias pertenecen a la sesión X11.
