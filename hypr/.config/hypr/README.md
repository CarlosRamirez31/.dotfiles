# Hyprland mínimo

Configuración para Hyprland 0.56 o posterior. Mantiene el estilo Catppuccin,
gaps, bordes redondeados, blur y animaciones, pero reduce la sesión a los
componentes necesarios para trabajar.

## Componentes

- Hyprland y UWSM: compositor y sesión.
- Foot: terminal sencilla y confiable.
- Rofi: launcher de aplicaciones.
- Waybar: barra existente del usuario.
- Awww: conserva el último wallpaper en caché.
- Hyprpolkitagent: diálogos de permisos gráficos.

No se inician aplicaciones personales, historial del portapapeles,
notificaciones, OSD, bloqueo, suspensión automática ni servicios AUR.

## Instalación

En Arch Linux:

```bash
sudo pacman -Syu
sudo pacman -S --needed \
  git stow hyprland uwsm xdg-desktop-portal-hyprland \
  foot rofi-wayland waybar awww hyprpolkitagent
```

Enlaza la configuración:

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
stow --restow hypr
```

En SDDM selecciona `Hyprland (uwsm-managed)`. Desde una TTY:

```bash
exec uwsm start hyprland.desktop
```

## Atajos

| Atajo | Acción |
| --- | --- |
| `Ctrl + Alt + T` | Abrir Foot |
| `Super + Enter` | Abrir Foot |
| `Alt + F2` | Abrir Rofi |
| `Super + Space` | Abrir Rofi |
| `Super + Q` | Cerrar ventana |
| `Super + F` | Pantalla completa |
| `Super + V` | Alternar ventana flotante |
| `Super + H/J/K/L` | Cambiar el foco |
| `Super + Shift + H/J/K/L` | Mover ventana |
| `Super + 1..9` | Cambiar de workspace |
| `Super + Shift + 1..9` | Mover ventana al workspace |
| `Super + Shift + E` | Cerrar la sesión |

## Estructura

```text
~/.config/hypr/
├── hyprland.lua
└── lua/
    ├── core.lua
    ├── theme.lua
    └── binds.lua
~/.config/foot/foot.ini
```

`core.lua` configura monitor, entrada y procesos esenciales. `theme.lua`
contiene exclusivamente la apariencia. `binds.lua` contiene los atajos.

## Validación

Después de actualizar:

```bash
hyprctl reload full-reset
hyprctl configerrors
```

`hyprctl configerrors` no debe mostrar errores.
