# Dotfiles

Escritorio Hyprland mínimo y reproducible para Arch Linux, con tema
Catppuccin/Tokyo Night, Ghostty, Rofi, HyprPanel y UWSM.

## Instalación limpia

Después de instalar Arch Linux y conectarte a Internet:

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles \
  && bash ~/.dotfiles/install.sh
```

Reinicia y selecciona `Hyprland (uwsm-managed)` en la pantalla de inicio.

## Aplicar cambios futuros

```bash
cd ~/.dotfiles
git pull --ff-only
bash install.sh
```

`install.sh` es idempotente: instala únicamente paquetes faltantes, conserva
el display manager existente, reaplica los enlaces administrados y refresca
Hyprland, HyprPanel y el wallpaper automáticamente cuando la sesión está
activa. Los paquetes visuales que no están en los repositorios oficiales se
instalan desde AUR con `paru`, `yay` o un `yay-bin` preparado por el script.
La configuración y los estilos editables de HyprPanel viven en
`templates/hyprpanel/`; el instalador crea copias de ejecución para que los
archivos generados por el panel no modifiquen el repositorio.

El instalador detecta VMware, VirtualBox, QEMU/KVM o hardware físico y aplica
únicamente la integración correspondiente. Los ajustes de compatibilidad y
latencia de VMware quedan limitados a la sesión de Hyprland; GNOME y otros
escritorios instalados en paralelo conservan su configuración normal.
