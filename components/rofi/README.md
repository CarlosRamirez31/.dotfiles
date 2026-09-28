# Rofi

Este componente instala el lanzador de aplicaciones y un wrapper adaptado a la sesión UWSM. Rofi usa entradas `.desktop`, iconos y caché XDG, por lo que puede iniciar aplicaciones gráficas sin mantener una lista manual.

## Uso

```bash
./install.sh rofi
dotfiles-app-launcher
rofi -show drun
```

Atajos equivalentes: `Alt+Space`, `Alt+D` y `Alt+F2`. Escribir filtra por nombre; Enter ejecuta la entrada seleccionada y Escape cancela.

## Por qué existe el wrapper

`.local/bin/dotfiles-app-launcher`:

1. aplica `GSK_RENDERER=cairo` solo en VMware para evitar fallos `vmwgfx`;
2. garantiza que `~/.local/bin` esté en `PATH` aunque SDDM entregue un entorno mínimo;
3. activa iconos y caché de aplicaciones;
4. ejecuta la línea `Exec` de la entrada directamente dentro de la sesión gráfica ya administrada por UWSM.

No envuelve cada aplicación en un nuevo proceso UWSM porque Hyprland ya pertenece a esa sesión. Esto también permite que D-Bus y portales resuelvan correctamente el display.

## Archivos y apariencia

| Archivo | Función |
| --- | --- |
| `.config/rofi/config.rasi` | Modo drun, fuente, posición y comportamiento. |
| `.config/rofi/theme.rasi` | Colores, espacios y redondeado coordinados. |
| `.local/bin/dotfiles-app-launcher` | Entorno y lanzamiento portable. |

## Diagnóstico

```bash
rofi -show drun -no-config
printf '%s\n' "$PATH"
find ~/.local/share/applications /usr/share/applications -name '*.desktop' | head
```

Si una aplicación recién instalada no aparece, ejecuta el wrapper otra vez: fuerza la recarga de la caché desktop. Si abre fuera de Wayland, verifica las variables exportadas por `uwsm`.
