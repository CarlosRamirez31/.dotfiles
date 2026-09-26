# Hyprland mínimo

Configuración para Hyprland 0.56 o posterior. Mantiene el estilo Catppuccin,
gaps, bordes redondeados, blur y animaciones, pero reduce la sesión a los
componentes necesarios para trabajar.

## Componentes

- Hyprland y UWSM: compositor y sesión.
- Foot: terminal sencilla y confiable.
- Rofi: launcher de aplicaciones.
- Waybar: barra Catppuccin compacta incluida.
- Awww: fondo Catppuccin oscuro y soporte para wallpapers.
- Hyprpolkitagent: diálogos de permisos gráficos.

No se inician aplicaciones personales, historial del portapapeles,
notificaciones, OSD, bloqueo, suspensión automática ni servicios AUR.

## Instalación

En una instalación de Arch Linux con conexión a Internet, ejecuta una sola vez:

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles \
  && bash ~/.dotfiles/install.sh
```

El instalador:

- instala exclusivamente los paquetes utilizados por esta configuración;
- respalda configuraciones locales anteriores con el sufijo `.backup.FECHA`;
- enlaza Hyprland, Foot, Rofi, Waybar y UWSM mediante Stow;
- activa NetworkManager;
- conserva el display manager existente o habilita SDDM si no existe uno.

Después reinicia y selecciona `Hyprland (uwsm-managed)` en la pantalla de
inicio. No es necesario ejecutar comandos para cargar la barra, el tema o el
fondo.

Para volver a aplicar una actualización futura:

```bash
cd ~/.dotfiles
git pull --ff-only
bash install.sh
```

El mismo script detecta los paquetes ya instalados y no vuelve a instalarlos.
Si se ejecuta dentro de Hyprland, recarga la configuración y reinicia Waybar
automáticamente; no hace falta ejecutar comandos adicionales ni reiniciar la
sesión para cambios normales de configuración.

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
~/.config/rofi/config.rasi
~/.config/waybar/config.jsonc
~/.config/waybar/style.css
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
