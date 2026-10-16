# Session

Este componente aporta bloqueo X11 y reglas conservadoras de suspensión. En
Awesome, Xss-lock observa el salvapantallas de X11 y ejecuta Betterlockscreen,
con el wallpaper Mocha difuminado y su interfaz de autenticación. Mientras se
instalan sus dependencias, Xsecurelock es el fallback seguro. No hay un segundo
temporizador DPMS que pueda dejar la pantalla negra al desbloquear. Las VMs no
se suspenden automáticamente.

## Instalación y bloqueo

```bash
./install.sh session
dotfiles-lock
dotfiles-sleep
dotfiles-can-suspend && echo permitida
```

`Ctrl+Shift+B` bloquea inmediatamente. Awesome configura un salvapantallas de
10 minutos y Xss-lock bloquea en ese momento. Betterlockscreen usa el wallpaper
seleccionado con efecto dim+blur y un prompt de contraseña minimalista.
`dotfiles-lock` no inicia una segunda instancia del locker.

En hardware físico, `dotfiles-sleep` suspende mediante systemd. En VMware solo
bloquea la sesión; para guardar el estado completo, suspende la VM desde el
hipervisor. `dotfiles-can-suspend` rechaza la suspensión automática en VMs y
cuando existe una conexión SSH entrante establecida.

## Archivos administrados

| Archivo | Función |
| --- | --- |
| `.local/bin/dotfiles-lock` | Inicio seguro del locker X11. |
| `.local/bin/dotfiles-lock-background` | Fondo de respaldo si falla la captura. |
| `.local/bin/dotfiles-sleep` | Suspensión física o bloqueo de VM. |
| `.local/bin/dotfiles-can-suspend` | Guarda contra VM y SSH. |
| `.local/bin/dotfiles-idle-brightness` | Atenuar/restaurar brillo cuando hay hardware compatible. |

## Diagnóstico

```bash
pgrep -a xss-lock
pgrep -a xsecurelock
xset q
systemd-detect-virt --vm
ss -Htn state established '( sport = :ssh )'
```

Este componente usa Xss-lock, Xsecurelock y XSet.
