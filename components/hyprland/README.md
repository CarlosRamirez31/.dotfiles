# Hyprland

Contiene el compositor y la gramática común de teclado del escritorio. La
configuración Lua está dividida en núcleo, apariencia, hardware y atajos. Solo
existen cuatro workspaces persistentes para coincidir con HyprPanel.

## Gramática de ventanas estilo Vim

| Atajo | Acción |
| --- | --- |
| `Super+H/J/K/L` | enfocar izquierda/abajo/arriba/derecha |
| `Super+Shift+H/J/K/L` | mover la ventana en esa dirección |
| `Super+Ctrl+H/J/K/L` | redimensionar en esa dirección |
| `Super+1..4` | cambiar de workspace |
| `Super+Shift+1..4` | mover al workspace y seguir la ventana |
| `Super+Q` | cerrar ventana |
| `Super+F` | pantalla completa |
| `Super+V` | alternar flotante |

La lógica refleja Neovim: `H/J/K/L` expresa dirección, `Shift` mueve y `Ctrl`
modifica el tamaño. No se agregan variantes con flechas para evitar memorizar
dos mapas equivalentes.

## Aplicaciones y sesión

| Atajo | Acción |
| --- | --- |
| `Super+Enter` / `Ctrl+Alt+T` | terminal |
| `Super+Space` / `Super+D` / `Alt+F2` | lanzador |
| `Super+B` | navegador |
| `Super+E` | archivos |
| `Super+C` | portapapeles |
| `Super+L` | bloqueo |
| `Super+Shift+E` | cerrar sesión |

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
