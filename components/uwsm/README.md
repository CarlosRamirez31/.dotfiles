# UWSM

UWSM inicia Hyprland como una sesión systemd de usuario, importa el entorno Wayland y agrupa aplicaciones/servicios en unidades administrables. Evita procesos gráficos huérfanos y asegura que D-Bus, portales y servicios vean el mismo display.

## Instalación y arranque

```bash
./install.sh uwsm
uwsm check may-start
```

Después de una instalación nueva, reinicia y selecciona `Hyprland (uwsm-managed)` en SDDM. No ejecutes simultáneamente `Hyprland` manual y la sesión UWSM.

## Variables exportadas

`.config/uwsm/env` define y finaliza:

| Variable | Motivo |
| --- | --- |
| `GDK_BACKEND=wayland,x11,*` | Preferir Wayland con fallback. |
| `GSK_RENDERER=cairo` solo en VMware | Evitar incompatibilidad de buffers GTK/vmwgfx. |
| `MOZ_ENABLE_WAYLAND=1` | Firefox nativo Wayland. |
| `ELECTRON_OZONE_PLATFORM_HINT=auto` | Selección correcta para Electron. |
| `PATH` con `~/.local/bin` | Scripts disponibles aun con entorno mínimo de SDDM. |
| `TERMINAL=dotfiles-terminal` | Terminal común para aplicaciones. |
| Variables `XDG_*` | Identificar Hyprland y Wayland. |
| Cursor Bibata, tamaño 24 | Apariencia coherente XCursor/Hyprland. |
| `SSH_AUTH_SOCK` | Agente SSH de GCR en el runtime del usuario. |

`.config/uwsm/env-hyprland` queda reservado para variables exclusivas de este compositor.

## Operación y diagnóstico

```bash
uwsm-app -- firefox          # aplicación dentro de la sesión gráfica
uwsm stop                    # cerrar la sesión completa
systemctl --user status graphical-session.target
systemctl --user list-units 'app-*'
systemctl --user show-environment | less
```

Hyprland ejecuta `uwsm finalize` al arrancar para publicar variables que solo existen cuando Wayland ya está activo. Si aplicaciones abiertas desde Rofi no ven display, compara `systemctl --user show-environment` con `env` y revisa el journal de usuario.
