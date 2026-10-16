# Session

Este componente aporta bloqueo X11 y reglas conservadoras de suspensión. En
Awesome, Xss-lock observa el salvapantallas de X11 y ejecuta Xsecurelock; DPMS
apaga las pantallas un minuto después. Las VMs no se suspenden automáticamente.

## Instalación y bloqueo

```bash
./install.sh session
dotfiles-lock
dotfiles-sleep
dotfiles-can-suspend && echo permitida
```

`Ctrl+Shift+B` bloquea inmediatamente. Awesome configura un salvapantallas de
10 minutos; Xss-lock bloquea en ese momento y DPMS se activa a los 11 minutos.
`dotfiles-lock` no inicia una segunda instancia de Xsecurelock.

En hardware físico, `dotfiles-sleep` suspende mediante systemd. En VMware solo
bloquea la sesión; para guardar el estado completo, suspende la VM desde el
hipervisor. `dotfiles-can-suspend` rechaza la suspensión automática en VMs y
cuando existe una conexión SSH entrante establecida.

## Archivos administrados

| Archivo | Función |
| --- | --- |
| `.local/bin/dotfiles-lock` | Inicio seguro de Xsecurelock. |
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
