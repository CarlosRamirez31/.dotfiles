# Dotfiles

Escritorio Hyprland mínimo y reproducible para Arch Linux. Cada programa tiene
su configuración y su instalador independiente; el instalador raíz solamente
los orquesta en un orden seguro.

## Instalación completa

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
./install.sh
```

El orden de la instalación completa es:

1. `system`: servicios base, audio, red y soporte de la máquina virtual.
2. `themes`: cursor Bibata e iconos Oranchelo.
3. `fonts`: fuente Lexend usada por el panel.
4. `uwsm`: variables de la sesión Wayland.
5. `alacritty`: terminal y su configuración visual.
6. `rofi`: lanzador de aplicaciones y su script auxiliar.
7. `wallpaper`: fondo y `awww`.
8. `hyprpanel`: barra, menús y notificaciones.
9. `hyprland`: compositor, atajos, reglas y tema de ventanas.

Los paquetes ya instalados se omiten mediante `pacman -Q` y `pacman --needed`.
Los archivos existentes que no pertenecen a este repositorio se renombran con
el sufijo `.backup.FECHA-HORA` antes de crear los enlaces administrados.

## Instalar solo una parte

Cada módulo funciona directamente:

```bash
./components/alacritty/install.sh
./components/hyprland/install.sh
```

También se pueden pedir varios al orquestador. El orden escrito no importa: el
script siempre los reordena según sus dependencias.

```bash
./install.sh hyprland alacritty rofi
```

Para ver los nombres disponibles:

```bash
./install.sh --help
```

## Estructura

```text
components/
  alacritty/   # ~/.config/alacritty
  fonts/       # ~/.local/share/fonts
  hyprland/    # ~/.config/hypr
  hyprpanel/   # plantilla copiada al directorio de ejecución
  rofi/        # ~/.config/rofi y lanzador
  system/      # paquetes y servicios del sistema
  themes/      # temas instalados desde AUR
  uwsm/        # ~/.config/uwsm
  wallpaper/   # ~/.config/wallpapers
scripts/
  lib.sh       # funciones compartidas por los instaladores
install.sh     # orquestador
```

Alacritty es el terminal predeterminado para `Ctrl+Alt+T`, `Super+Enter` y el
clic central del panel. Se abre sin barra de título ni decoración del sistema,
con el mismo estilo limpio de la configuración anterior.

Después de una instalación limpia, reinicia y selecciona
`Hyprland (uwsm-managed)` en la pantalla de inicio.
