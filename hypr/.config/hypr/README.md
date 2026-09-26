# Hyprland dots

Configuración modular en Lua, migrada y validada estáticamente para Hyprland
0.56.2. Conserva el tema Catppuccin, los atajos, las reglas de ventanas y el
flujo de trabajo original, pero ya no depende del formato legacy
`hyprland.conf`. La separación por módulos hace que los próximos cambios de API
se puedan aislar sin rehacer toda la configuración.

## Qué instala y qué no

Este repositorio configura el entorno gráfico; no instala automáticamente un
arsenal de pentesting ni habilita repositorios de terceros. Esa separación es
intencional: mantiene el sistema base reproducible y permite elegir después
Kali tools, BlackArch o herramientas concretas sin mezclar su mantenimiento con
Hyprland.

- **Esencial para la sesión:** Hyprland, UWSM, portal, Waybar, notificaciones,
  bloqueo, audio, red, launcher, portapapeles y capturas.
- **Aplicaciones personales:** Zen, Vesktop, Obsidian y YouTube Music. Mantienen
  sus atajos, pero puedes omitirlas; su ausencia no impide iniciar Hyprland.
- **Opcional:** XDM, arrpc, emoji picker y clima. No son necesarios para el
  escritorio ni para pentesting.
- **No incluido:** drivers de GPU, display manager y herramientas de seguridad,
  porque dependen del hardware y del laboratorio que vayas a montar.

## Requisitos

Esta guía asume Arch Linux y un usuario con `sudo`. Antes de continuar, instala
el controlador de tu GPU siguiendo la [tabla oficial de ArchWiki](https://wiki.archlinux.org/title/Xorg#Driver_installation).
No se fija un driver en estos dotfiles porque AMD, Intel, NVIDIA, una VM y equipos
híbridos necesitan paquetes distintos. Actualiza el sistema antes de instalar y
no mezcles paquetes estables de Hyprland con variantes `-git`.

### Repositorios oficiales

```bash
sudo pacman -Syu
sudo pacman -S --needed \
  git stow hyprland uwsm xdg-desktop-portal-hyprland \
  hypridle hyprlock waybar swaync swww swappy grim slurp \
  ghostty nautilus rofi-wayland fuzzel \
  wl-clipboard cliphist brightnessctl wireplumber playerctl \
  networkmanager network-manager-applet bluez bluez-utils \
  polkit-gnome curl libnotify kcalc xdg-user-dirs \
  ttf-jetbrains-mono-nerd
```

Activa los servicios del sistema que usa la configuración:

```bash
sudo systemctl enable --now NetworkManager.service
sudo systemctl enable --now bluetooth.service
xdg-user-dirs-update
```

### AUR

En una instalación nueva, instala primero las herramientas de compilación y
construye `paru` desde su PKGBUILD (revísalo antes de ejecutar `makepkg`):

```bash
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/paru.git /tmp/paru
cd /tmp/paru
makepkg -si
```

Luego instala los paquetes AUR:

```bash
paru -S --needed \
  grimblast-git swayosd-git wl-clipboard-history \
  bibata-cursor-theme-bin zen-browser-bin \
  youtube-music-bin vesktop-bin obsidian
```

`fuzzel-emoji`, `xdm-app` y `~/.local/scripts/arrpc` son opcionales. Los dos
últimos solo se inician cuando existen. Si no instalas `fuzzel-emoji`, el atajo
`SUPER + comma` no hará nada hasta que cambies su comando en
`~/.config/hypr/lua/binds.lua`.

Hyprlock usa `Google Sans`, `PP Neue Machina` y Nerd Font. Si las dos primeras no
están instaladas, el lockscreen usará una fuente sustituta; esto no impide iniciar
Hyprland.

El clima está desactivado por privacidad: la configuración no geolocaliza tu IP.
Si quieres activarlo, escribe `CITY` y opcionalmente `COUNTRY` al principio de
`~/.config/hypr/hyprlock.conf`; solo entonces se consulta `wttr.in`, cada 30
minutos mientras el lockscreen esté abierto.

## Instalación

Haz una copia de cualquier configuración previa antes de enlazar estos archivos:

```bash
backup_id=$(date +%Y%m%d-%H%M%S)
[ ! -e ~/.config/hypr ] || mv ~/.config/hypr ~/.config/hypr.backup.$backup_id
mkdir -p ~/.config/uwsm
[ ! -e ~/.config/uwsm/env ] || mv ~/.config/uwsm/env ~/.config/uwsm/env.backup.$backup_id
[ ! -e ~/.config/uwsm/env-hyprland ] || mv ~/.config/uwsm/env-hyprland ~/.config/uwsm/env-hyprland.backup.$backup_id
```

Clona el repositorio y crea los enlaces con GNU Stow:

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
stow --restow hypr
```

El paquete `hypr` instala:

```text
~/.config/hypr/hyprland.lua   configuración principal
~/.config/hypr/lua/           módulos de opciones, tema, binds y reglas
~/.config/hypr/hyprlock.conf  lockscreen
~/.config/hypr/hypridle.conf  inactividad y suspensión
~/.config/uwsm/               variables de entorno de la sesión
```

Los monitores usan `preferred`, posición automática y escala automática. Esto
permite arrancar con panel interno, HDMI, DisplayPort, una VM o una resolución
desconocida. Después puedes fijar una distribución concreta en
`~/.config/hypr/lua/monitors.lua` si la necesitas.

## Iniciar la sesión

La configuración usa UWSM. En SDDM u otro display manager selecciona
`Hyprland (uwsm-managed)`. Desde una TTY puedes iniciar directamente con:

```bash
exec uwsm start hyprland.desktop
```

Si quieres SDDM en una instalación que todavía no tiene display manager:

```bash
sudo pacman -S --needed sddm
sudo systemctl enable sddm.service
```

No habilites SDDM si ya utilizas otro display manager.

## Perfil de pentesting opcional

Primero deja estable el escritorio y después instala las herramientas por
familias. Este punto de partida usa únicamente repositorios oficiales de Arch:

```bash
sudo pacman -S --needed \
  nmap wireshark-qt tcpdump openbsd-netcat bind whois traceroute \
  python python-pipx sqlmap gobuster
```

No se instala el grupo completo de BlackArch: añade una superficie enorme de
paquetes, conflictos y actualizaciones que no todo pentester necesita. Agrega
después solo las herramientas de tus laboratorios autorizados. Para capturar con
Wireshark sin abrir toda la aplicación como root:

```bash
sudo usermod -aG wireshark "$USER"
```

Cierra la sesión y vuelve a entrar para aplicar el grupo.

## Validación y diagnóstico

Dentro de Hyprland, recarga y consulta cualquier error:

```bash
hyprctl reload full-reset
hyprctl configerrors
```

`hyprctl configerrors` no debe imprimir nada. Para revisar la versión y el log de
la sesión UWSM:

```bash
hyprctl version
journalctl --user -b --grep='hyprland\|uwsm' --no-pager
```

Si actualizas Hyprland, consulta primero la documentación correspondiente a tu
tag (`hyprctl version`) y valida de nuevo con los comandos anteriores.

## Personalización rápida

- Monitores: `~/.config/hypr/lua/monitors.lua`
- Programas y atajos: `~/.config/hypr/lua/binds.lua`
- Tema y animaciones: `~/.config/hypr/lua/theme.lua`
- Reglas de ventanas y capas: `~/.config/hypr/lua/rules.lua`
- Programas al iniciar: `~/.config/hypr/lua/autostart.lua`
- Entrada, gesto y opciones generales: `~/.config/hypr/lua/options.lua`

Para desinstalar únicamente los enlaces creados por Stow:

```bash
cd ~/.dotfiles
stow -D hypr
```
