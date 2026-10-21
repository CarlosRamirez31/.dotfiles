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

## Recuperación de la NVIDIA en LOQ 15AHP9

En el LOQ 15AHP9 con RTX 4050 (`10de:28e1`) se verificó un ciclo de
reactivaciones ACPI GPE10 del puerto GPP0 después de suspender la GPU.
La limpieza de salidas desconectadas corresponde a `dotfiles-display`.
El servicio opcional de recuperación espera 10 segundos después de desconectar
el último monitor, observa 20 segundos y actúa únicamente si detecta al menos
dos eventos GPE10, actividad predominante y entradas breves en suspensión.
También hace una comprobación al iniciar sin monitores externos.

Lee estados de sysfs cada dos segundos sin consultar XRandR ni abrir la GPU.
Solo actúa cuando las salidas externas están desconectadas y apagadas.
Deshabilita GPE10 durante un máximo de 15 segundos y lo vuelve a habilitar;
si detecta una reconexión termina antes. Hace como máximo un intento por
desconexión y deja al menos 60 segundos entre intentos. El estado se restaura
al detenerse y mediante `ExecStopPost` si el proceso termina abruptamente.
No incluye todavía un tratamiento especial de suspensión/reanudación del equipo.

Desde la raíz del repositorio, instalar explícitamente:

```bash
sudo python3 components/session/dotfiles/.local/share/gpu-recovery/install.py
systemctl status dotfiles-gpu-recovery.service --no-pager
journalctl -u dotfiles-gpu-recovery.service -b --no-pager
```

El instalador comprueba el hardware y copia el programa y el servicio como
archivos propiedad de root; no ejecuta código desde el directorio del usuario
en segundo plano. Para retirarlo y restaurar GPE10 si corresponde:

```bash
sudo python3 components/session/dotfiles/.local/share/gpu-recovery/install.py --uninstall
```

Pruebas: `python3 -m unittest discover -s components/session/tests`.
