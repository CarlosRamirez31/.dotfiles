# Hyprland mínimo

Configuración para Hyprland 0.56 o posterior. Adapta el diseño Catppuccin del
repositorio de referencia a la configuración Lua actual y conserva únicamente
los componentes necesarios para reproducir su aspecto.

La salida virtual utiliza 1920×1080 a 60 Hz, posición 0×0 y escala 1 para
evitar que una resolución invitada de 1280×800 quede rodeada por franjas negras
en la consola de la máquina virtual.

## Componentes

- Hyprland y UWSM: compositor y sesión.
- Ghostty: terminal con JetBrains Mono Nerd Font y Tokyo Night.
- Rofi: launcher Catppuccin con iconos Oranchelo.
- HyprPanel: barra flotante con módulos Catppuccin.
- Awww: carga el wallpaper Arch BSOD versionado en el repositorio.
- Lexend y Bibata: tipografía de la barra y cursor.
- Hyprpolkitagent: diálogos de permisos gráficos.

No se instalan Fish, Starship, Nitch, aplicaciones personales, historial del
portapapeles, bloqueo ni suspensión automática.

Ghostty abre centrado y flotante al 72 % del monitor. Puede alternarse a modo
mosaico con `Super + V`.

## Instalación

En una instalación de Arch Linux con conexión a Internet, ejecuta una sola vez:

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles \
  && bash ~/.dotfiles/install.sh
```

El instalador:

- instala exclusivamente los paquetes utilizados por esta configuración;
- respalda configuraciones locales anteriores con el sufijo `.backup.FECHA`;
- instala los paquetes AUR visuales solamente cuando faltan;
- enlaza Hyprland, Ghostty, HyprPanel, Rofi, fuentes, wallpaper y UWSM mediante
  Stow;
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
Si se ejecuta dentro de Hyprland, recarga la configuración, reinicia HyprPanel
y reaplica el wallpaper automáticamente; no hace falta ejecutar comandos
adicionales ni reiniciar la sesión para cambios normales de configuración.

## Atajos

| Atajo | Acción |
| --- | --- |
| `Ctrl + Alt + T` | Abrir Ghostty |
| `Super + Enter` | Abrir Ghostty |
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
~/.config/ghostty/config
~/.config/hyprpanel/config.json  # copia generada desde templates/hyprpanel/
~/.config/rofi/config.rasi
~/.config/rofi/theme.rasi
~/.config/wallpapers/arch-bsod.png
~/.local/share/fonts/Lexend/
```

`core.lua` configura monitor, entrada y procesos esenciales. `theme.lua`
contiene exclusivamente la apariencia. `binds.lua` contiene los atajos.
HyprPanel escribe archivos durante su ejecución, por lo que su configuración
versionada se conserva como plantilla fuera del paquete de Stow.

## Validación

Después de actualizar:

```bash
hyprctl reload full-reset
hyprctl configerrors
```

`hyprctl configerrors` no debe mostrar errores.
