# Hyprland

Contiene el compositor y la gramática común de teclado del escritorio. La
configuración Lua está dividida en núcleo, apariencia, hardware y atajos. Solo
existen cuatro workspaces persistentes para coincidir con HyprPanel.

## Gramática de ventanas estilo Vim

| Atajo | Acción |
| --- | --- |
| `Alt+H/J/K/L` | enfocar izquierda/abajo/arriba/derecha |
| `Alt+Shift+H/J/K/L` | mover la ventana en esa dirección |
| `Alt+Ctrl+H/J/K/L` | redimensionar en esa dirección |
| `Alt+1..4` | cambiar de workspace |
| `Alt+Shift+1..4` | mover al workspace y seguir la ventana |
| `Alt+Q` | cerrar ventana |
| `Alt+F` | pantalla completa |
| `Alt+V` | alternar flotante |

La lógica refleja Neovim: `H/J/K/L` expresa dirección, `Shift` mueve y `Ctrl`
modifica el tamaño. Se usa `Alt` en vez de `Super` para evitar atajos del
Windows anfitrión en una VM.

## Aplicaciones y sesión

| Atajo | Acción |
| --- | --- |
| `Alt+Enter` / `Ctrl+Alt+T` | terminal |
| `Alt+Space` / `Alt+D` / `Alt+F2` | lanzador |
| `Alt+B` | navegador |
| `Alt+E` | archivos |
| `Alt+C` | portapapeles |
| `Ctrl+Shift+B` | bloqueo |
| `Alt+Shift+E` | cerrar sesión |

Las capturas y grabación se documentan en `desktop-tools` y `desktop-extras`.

## Monitores y validación

La regla general usa el modo preferido. Para un equipo específico copia
`~/.config/hypr/local.lua.example` a `~/.config/hypr/local.lua`; el archivo
local se ignora en Git.

```bash
hyprctl monitors all
hyprctl reload
hyprctl configerrors
```
