# Dotfiles

Escritorio Hyprland mínimo y reproducible para Arch Linux, con tema
Catppuccin, Foot, Rofi, Waybar y UWSM.

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
Hyprland y Waybar automáticamente cuando la sesión está activa.
