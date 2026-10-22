# Rofi

Este componente instala el lanzador de aplicaciones y el menú de sesión para
Awesome/X11. Rofi usa entradas `.desktop`, iconos y la caché XDG.

## Uso

```bash
./install.sh rofi
dotfiles-app-launcher
rofi -show drun
```

Atajos equivalentes: `Alt+Space`, `Alt+D` y `Alt+F2`. Escribir filtra por
nombre; Enter ejecuta la aplicación seleccionada y Escape cancela.

## Wrapper y apariencia

`.local/bin/dotfiles-app-launcher` asegura que `~/.local/bin` esté en `PATH`,
activa iconos y refresca la caché de aplicaciones. Ejecuta las entradas dentro
del display X11 actual.

| Archivo | Función |
| --- | --- |
| `.config/rofi/config.rasi` | Modo drun, fuente, posición y comportamiento. |
| `.config/rofi/theme.rasi` | Colores y espacios Catppuccin. |
| `.local/bin/dotfiles-app-launcher` | Entorno y lanzamiento portable. |

## Diagnóstico

```bash
command -v rofi dotfiles-app-launcher
printf 'session=%s display=%s\n' "$XDG_SESSION_TYPE" "$DISPLAY"
find ~/.local/share/applications /usr/share/applications -name '*.desktop' | head
```

Si una aplicación recién instalada no aparece, vuelve a abrir el wrapper para
recargar la caché. En Awesome `XDG_SESSION_TYPE` debe ser `x11`.
