# Session

Gestiona bloqueo, inactividad y energía con Hyprlock e Hypridle. El bloqueo usa
la misma paleta Tokyo Night, reloj grande y fondo difuminado. La pantalla se
atenúa a los 5 minutos, se bloquea a los 10, apaga monitores a los 11 y puede
suspender un equipo físico a los 30 minutos.

En VMware, `dotfiles-lock` usa Gtklock porque Hyprlock 0.9.6 aborta al adquirir
el bloqueo de sesión con Hyprland 0.56.x y `vmwgfx`. Gtklock muestra un campo de
contraseña explícito; en equipos físicos se conserva la pantalla temática de
Hyprlock. El tema de Gtklock reutiliza el wallpaper y la paleta Catppuccin de
Rofi/HyprPanel; vive en `.config/gtklock/style.css` y `layout.xml`.

La suspensión automática se omite en máquinas virtuales y cuando existe una
sesión SSH entrante activa, evitando perder una máquina de trabajo remota. En
portátiles instala `power-profiles-daemon`, salvo que TLP ya esté administrando
la energía.

## Uso

```bash
./install.sh session
loginctl lock-session
systemctl --user status dotfiles-hypridle.service
```

Atajo: `Ctrl+Shift+B` bloquea inmediatamente. Los tiempos se cambian en
`.config/hypr/hypridle.conf`.
