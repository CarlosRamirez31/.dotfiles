# Dotfiles

Escritorio Arch Linux reproducible para programación, uso diario y laboratorios
de seguridad autorizados. El conjunto usa AwesomeWM sobre X11, Alacritty, Zsh y
Neovim con una apariencia coherente y módulos instalables por separado.

La configuración prioriza cuatro ideas:

- instalar solamente lo que cada módulo necesita;
- no reinstalar paquetes que ya existen;
- respaldar archivos ajenos antes de enlazar los administrados;
- mantener identidades, contraseñas y ajustes por máquina fuera de Git.

## Instalación

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
./install.sh
```

El instalador requiere Arch Linux, se ejecuta como usuario normal y solicita la
contraseña de `sudo` una vez al comenzar. Mantiene esa autorización solamente
mientras se ejecuta. Pacman acepta automáticamente cada transacción y usa los
proveedores predeterminados de Arch; no hay que responder selectores y los
dotfiles no fijan un proveedor innecesario. Al terminar, reinicia y selecciona
`Awesome` en SDDM. El componente `system` instala y habilita SDDM para el
próximo arranque sin interrumpir la sesión actual.

Para instalar componentes concretos:

```bash
./install.sh rofi alacritty awesome
./install.sh --help
```

El orden escrito no importa: el orquestador siempre respeta las dependencias.

## Módulos

| Módulo | Para qué existe |
| --- | --- |
| [`system`](components/system/README.md) | red, audio, portal GTK/X11, OpenVPN, SDDM y soporte de VM |
| [`themes`](components/themes/README.md) | cursor Bibata e iconos Oranchelo |
| [`fonts`](components/fonts/README.md) | JetBrainsMono Nerd Font y Lexend |
| [`shell`](components/shell/README.md) | Zsh, Starship, historial, navegación y herramientas de red |
| [`fastfetch`](components/fastfetch/README.md) | resumen visual del sistema al abrir terminal |
| [`maintenance`](components/maintenance/README.md) | revisión segura, caché de Pacman y TRIM |
| [`quality`](components/quality/README.md) | validación reproducible de Bash, Zsh, JSON y Lua |
| [`git-security`](components/git-security/README.md) | Git portable, identidad privada y firma SSH opcional |
| [`backup`](components/backup/README.md) | copias cifradas y verificables con Restic |
| [`workbench`](components/workbench/README.md) | entornos rootless de desarrollo y pentesting |
| [`desktop-extras`](components/desktop-extras/README.md) | Firefox, KeePassXC, Btop, grabación, color y papelera |
| [`session`](components/session/README.md) | bloqueo, inactividad, suspensión y energía |
| [`desktop-tools`](components/desktop-tools/README.md) | capturas e historial del portapapeles |
| [`files`](components/files/README.md) | Yazi, selector del sistema, Thunar, visores y asociaciones |
| [`hardware`](components/hardware/README.md) | Bluetooth y, en equipos físicos, firmware/SMART |
| [`security`](components/security/README.md) | keyring, agente SSH y firewall nftables |
| [`alacritty`](components/alacritty/README.md) | terminal gráfica y registro XDG |
| [`nvim`](components/nvim/README.md) | editor LazyVim para todos los lenguajes usados |
| [`rofi`](components/rofi/README.md) | lanzador de aplicaciones |
| [`wallpaper`](components/wallpaper/README.md) | carrusel GTK/X11 y fondo Feh |
| [`awesome`](components/awesome/README.md) | sesión X11, Wibar, notificaciones y Picom |
| [`doctor`](components/doctor/README.md) | diagnóstico final de toda la instalación |

Cada README enlazado explica sus archivos, decisiones y los pocos comandos que
realmente forman parte de su uso.

## Gramática del teclado

Los atajos evitan `Super` para no activar combinaciones del Windows anfitrión
cuando el escritorio se ejecuta dentro de una máquina virtual:

| Atajo | Acción |
| --- | --- |
| `Alt+H/J/K/L` | enfocar izquierda/abajo/arriba/derecha |
| `Alt+Shift+H/J/K/L` | mover ventana |
| `Alt+Ctrl+H/J/K/L` | redimensionar ventana |
| `Alt+1..4` | cambiar entre los cuatro workspaces |
| `Alt+Shift+1..4` | mover ventana al workspace |
| `Alt+Q` | cerrar ventana |
| `Alt+F` | pantalla completa |
| `Alt+V` | alternar flotante |

Aplicaciones y sesión:

| Atajo | Acción |
| --- | --- |
| `Alt+Enter` / `Ctrl+Alt+T` | terminal |
| `Alt+Space` / `Alt+D` / `Alt+F2` | aplicaciones |
| `Alt+B` | Firefox |
| `Alt+E` | Yazi |
| `Ctrl+Alt+E` | Thunar (respaldo gráfico) |
| `Alt+W` | seleccionar wallpaper con vista previa |
| `Alt+C` | historial del portapapeles |
| `Ctrl+Shift+B` | bloquear |
| `Alt+Shift+E` | cerrar sesión |

Captura y utilidades:

| Atajo | Acción |
| --- | --- |
| `Print` | capturar pantalla completa |
| `Alt+Print` | capturar región |
| `Alt+Shift+S` | capturar región y editar |
| `Alt+Shift+R` | iniciar/detener grabación de región |
| `Alt+Shift+C` | copiar color de la pantalla |

Las teclas físicas controlan volumen, micrófono, brillo y reproducción incluso
con la pantalla bloqueada.

## Comandos cotidianos

```bash
doctor                       # comprobar toda la instalación
maintain check               # servicios, disco y actualizaciones
maintain clean               # caché segura y journal de usuario
backup run                   # ejecutar respaldo ya configurado
distrobox enter dev         # entrar al entorno de desarrollo
distrobox enter kalilinux   # entrar al entorno Kali
distrobox enter parrotos    # entrar al entorno ParrotOS, si fue creado
sysinfo                      # información visual del sistema
```

Los comandos especializados restantes están en el README de su módulo; no se
repiten aquí para mantener una referencia corta.

## Configuración privada posterior

La instalación general queda funcional, pero estas dos decisiones no deben
inventarse ni publicarse en el repositorio.

Identidad Git:

```bash
git identity setup "Tu Nombre" correo@example.com
```

Para firmar commits con una llave SSH pública:

```bash
git identity setup "Tu Nombre" correo@example.com ~/.ssh/id_ed25519.pub
```

Destino cifrado de respaldo:

```bash
backup setup /ruta/al/repositorio-restic
backup run
```

`backup.conf`, la contraseña de Restic, la identidad Git y `local.lua` están
ignorados por Git.

## HTB y OpenVPN

La Wibar de Awesome muestra el icono verde de HTB y la IP cuando detecta la VPN. Puedes
fijar la máquina objetivo con:

```bash
htb-target 10.10.11.20
htb-target clear
```

Ping, Nmap, HTTP y SSH hacia HTB funcionan normalmente. Solo hace falta una
regla extra cuando la máquina remota inicia una conexión nueva hacia tu
listener:

```bash
lab-firewall lab-open tcp 4444
rlwrap nc -lvnp 4444
lab-firewall lab-close tcp 4444
```

Ese puerto solo se expone en interfaces VPN `tun*` y desaparece al reiniciar o
recargar nftables.

## Contenedores de trabajo

Los contenedores no se crean automáticamente ni consumen espacio hasta que los
pidas:

```bash
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name dev
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name kalilinux
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name parrotos
distrobox list
```

Podman funciona rootless. Distrobox integra el home, pero mantiene compiladores
y herramientas específicas fuera del sistema Arch principal.

## Monitores

Awesome usa la salida disponible y su modo preferido. Consulta las salidas y
modos reales antes de cambiar resolución o posición:

```bash
xrandr --query
xrandr --output NOMBRE_REAL --mode 1920x1080 --rate 60
```

Sustituye `NOMBRE_REAL` por el nombre reportado por XRandR; no copies ese ajuste
a un equipo con salidas distintas.

## Windows y Neovim

El módulo Neovim conserva instalación independiente para Windows:

```powershell
.\components\nvim\install.ps1
```

La configuración de Flutter detecta Android SDK y emuladores mediante variables
y rutas estándar en Windows, Linux y macOS; no depende de un nombre de usuario.

## Mantenimiento del repositorio

Los paquetes existentes se omiten mediante `pacman -Q` y `pacman --needed`.
GNU Stow crea enlaces hacia el repositorio; si encuentra un archivo ajeno, lo
renombra con `.backup.FECHA-HORA`. Las configuraciones locales y secretos nunca
se reemplazan deliberadamente.

Después de cualquier cambio importante:

```bash
./check.sh
doctor
git status
```
