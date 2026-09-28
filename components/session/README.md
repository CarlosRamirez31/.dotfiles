# Session

Este componente coordina bloqueo, inactividad, brillo, suspensión y energía. Su objetivo es proteger una sesión desatendida sin suspender una VM o cortar administración SSH activa.

## Paquetes y servicio

Instala Hyprlock, Hypridle y Gtklock. En portátiles detectados por `/sys/class/power_supply/BAT*`, conserva TLP si ya existe; en caso contrario instala y habilita `power-profiles-daemon`. En equipos sin batería no añade un gestor de perfiles.

`dotfiles-hypridle.service` pertenece a `graphical-session.target`, reinicia tras fallos y solo se reinicia durante la instalación si hay Wayland activo.

## Línea de tiempo de inactividad

| Tiempo | Acción |
| --- | --- |
| 5 min | Guarda brillo actual y baja a 10 %. |
| Reanudar actividad | Restaura el valor exacto guardado. |
| 10 min | Bloquea mediante `loginctl`. |
| 11 min | Apaga monitores con DPMS; los reactiva al volver. |
| 30 min | Suspende solo si `dotfiles-can-suspend` lo permite. |

Antes de una suspensión externa se bloquea; después se encienden monitores. La suspensión automática se rechaza en cualquier VM y cuando existe una conexión SSH entrante establecida.

## Bloqueo y compatibilidad VMware

```bash
dotfiles-lock
loginctl lock-session
```

En hardware físico, `dotfiles-lock` ejecuta Hyprlock con captura difuminada, reloj, usuario y campo de contraseña Tokyo Night. En VMware usa Gtklock porque Hyprlock 0.9.6/Hyprland 0.56.x puede abortar al adquirir el session-lock sobre `vmwgfx`. Evita iniciar un segundo locker si ya existe uno.

`Ctrl+Shift+B` bloquea de inmediato. Los archivos Gtklock reutilizan el wallpaper y proporcionan campo explícito de contraseña.

## Suspensión manual

```bash
dotfiles-sleep
dotfiles-can-suspend && echo permitida
```

En equipo físico, `dotfiles-sleep` llama a `systemctl suspend`. En VM solo bloquea: para guardar el estado completo se usa Suspend del hipervisor anfitrión, evitando fallos gráficos al reanudar.

## Archivos administrados

| Archivo | Función |
| --- | --- |
| `.config/hypr/hypridle.conf` | Tiempos y acciones. |
| `.config/hypr/hyprlock.conf` | Pantalla de bloqueo física. |
| `.config/gtklock/{style.css,layout.xml}` | Fallback VMware. |
| `.local/bin/dotfiles-lock` | Selección segura del locker. |
| `.local/bin/dotfiles-sleep` | Suspender físico/bloquear VM. |
| `.local/bin/dotfiles-can-suspend` | Guarda contra VM y SSH. |
| `.local/bin/dotfiles-idle-brightness` | Guardar/restaurar brillo. |

## Diagnóstico

```bash
systemctl --user status dotfiles-hypridle.service
journalctl --user -u dotfiles-hypridle.service -b
systemd-detect-virt --vm
ss -Htn state established '( sport = :ssh )'
brightnessctl get
```
