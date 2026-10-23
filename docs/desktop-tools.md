# Desktop tools

Implementa capturas e historial del portapapeles para X11. Maim captura, Slop
selecciona regiones, Xclip integra el portapapeles y
Clipmenu guarda el historial que Rofi presenta bajo demanda.

## Dependencias

| Paquete | Función |
| --- | --- |
| `maim` | Captura completa o de una región X11. |
| `slop` | Selecciona la región para captura. |
| `xclip` | Copia imágenes y texto al portapapeles X11. |
| `clipmenu` | Historial del portapapeles con `clipmenud` y Rofi. |
| `python` | Menú con límite de historial y entradas fijadas. |

## Capturas

```bash
./install.sh desktop-tools
dotfiles-screenshot full
dotfiles-screenshot area
```

Las imágenes se guardan con fecha y hora en `$(xdg-user-dir PICTURES)/Screenshots`
y se copian al portapapeles.

| Atajo | Acción |
| --- | --- |
| `Print` | Pantalla completa. |
| `Alt+Print` | Seleccionar región. |
| `Alt+Shift+S` | Capturar una región. |

## Portapapeles

```bash
dotfiles-clipboard
dotfiles-clipboard-clear
```

`Alt+C` abre el historial en Rofi. Elegir una entrada con Enter la copia al
portapapeles y la pega en la ventana original, usando `Ctrl+Shift+V` en
Alacritty y otras terminales, o `Ctrl+V` en aplicaciones gráficas. Requiere
`xdotool` y `xorg-xprop`. Awesome inicia `clipmenud` automáticamente para
guardar las copias explícitas del portapapeles. No registra la selección
del ratón (PRIMARY), para evitar capturas continuas al seleccionar texto.
`Alt+C` también inicia el capturador si no está funcionando, sin necesidad
de reiniciar el escritorio. Las nuevas copias se guardan desde ese momento.
Se conservan hasta 100 entradas recientes (se recortan por lotes a 90) y
20 fijadas. `Ctrl+P` fija o desfija la entrada seleccionada; las fijadas
aparecen primero con ★ y se guardan en `~/.local/state/dotfiles/clipboard`
(o `$XDG_STATE_HOME/dotfiles/clipboard`). Sobreviven a reinicios y a la
limpieza del historial. La limpieza exige confirmar en Rofi.

## Diagnóstico

```bash
command -v maim slop xclip clipmenu clipmenud
pgrep -a -u "$USER" -f '[c]lipmenud'
journalctl --user -b | rg -i 'clipmenu|maim'
```

Todos sus procesos y dependencias pertenecen a la sesión X11.

## Fuentes del módulo

Instalador: [`setup/modules/desktop-tools.sh`](../setup/modules/desktop-tools.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
