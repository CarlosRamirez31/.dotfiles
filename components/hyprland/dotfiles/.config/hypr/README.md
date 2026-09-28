# Hyprland

Este directorio contiene exclusivamente la configuración del compositor:
monitor, entrada, cursor, tema de ventanas, animaciones, atajos y procesos que
deben arrancar con la sesión.

## Archivos

- `hyprland.lua`: punto de entrada.
- `lua/core.lua`: monitor, entrada, renderizado y arranque de sesión.
- `lua/theme.lua`: bordes, espacios, animaciones y reglas de ventanas.
- `lua/binds.lua`: atajos del teclado y ratón.
- `lua/hardware.lua`: detección mínima de VMware para sus ajustes gráficos.

Alacritty, Rofi, UWSM, HyprPanel, fuentes y wallpaper viven en sus propios
módulos bajo `components/`; no se administran desde este directorio.

## Atajos

| Atajo | Acción |
| --- | --- |
| `Ctrl + Alt + T` | Abrir Alacritty |
| `Super + Enter` | Abrir Alacritty |
| `Alt + F2` / `Super + Space` | Abrir Rofi |
| `Super + Q` | Cerrar ventana |
| `Super + F` | Alternar pantalla completa |
| `Super + V` | Alternar ventana flotante |
| `Super + H/J/K/L` | Cambiar el foco |
| `Super + Shift + H/J/K/L` | Mover ventana |
| `Super + 1..4` | Cambiar de workspace |
| `Super + Shift + 1..4` | Mover ventana al workspace |
| `Super + Shift + E` | Cerrar la sesión |

Instalación independiente:

```bash
./components/hyprland/install.sh
```

Para validar dentro de una sesión activa:

```bash
hyprctl reload
hyprctl configerrors
```
