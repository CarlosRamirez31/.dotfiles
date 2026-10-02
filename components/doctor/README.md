# Doctor

`dotfiles-doctor` es la comprobación integral y de solo lectura del escritorio. Distingue una instalación rota de una función opcional pendiente. Su instalador enlaza el script y lo ejecuta inmediatamente al final del despliegue.

## Uso y resultado

```bash
./install.sh doctor
doctor
doctor >/tmp/doctor.txt
```

- `✓`: requisito presente o estado esperado.
- `!`: función opcional ausente/inactiva o prueba en vivo no disponible.
- `✗`: requisito esencial roto.

Sale con código `1` cuando hay errores y `0` cuando la base funciona, aunque existan advertencias.

## Qué comprueba

1. Comandos esenciales: Hyprland, UWSM, Zsh, Alacritty, Neovim, Rofi, HyprPanel, Hyprlock e Hypridle.
2. Resolución exacta de JetBrainsMono Nerd Font, Noto Color Emoji para símbolos de Starship y Lexend para HyprPanel.
3. Herramientas opcionales de archivos, capturas, red, backup, contenedores y uso diario.
4. Que Zsh sea el shell de login.
5. Que configuraciones críticas sean enlaces Stow válidos.
6. NetworkManager, nftables, timers de Pacman/TRIM y Bluetooth según hardware.
7. Sockets de GNOME Keyring/GCR y disponibilidad de Podman/`labbox`.
8. Si Restic e identidad Git privada ya se configuraron.
9. En Hyprland activo: errores de configuración y servicios Cliphist/Hypridle.

## Límites

No modifica archivos, instala paquetes ni reinicia servicios. Restic o Git pendientes son informativos porque requieren decisiones privadas. Fuera de Hyprland no puede ejecutar pruebas en vivo y emite advertencia.

## Diagnóstico complementario

```bash
systemctl --failed
systemctl --user --failed
hyprctl configerrors
systemctl --user status dotfiles-hypridle.service
git status
```

El único archivo administrado es `.local/bin/dotfiles-doctor`; no tiene paquetes propios porque inspecciona los demás componentes.
