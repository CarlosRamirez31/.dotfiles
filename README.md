# Dotfiles

Escritorio Arch Linux reproducible para programación, uso diario y laboratorios
de seguridad autorizados. El conjunto usa Hyprland, HyprPanel, Alacritty, Zsh y
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

El instalador requiere Arch Linux, se ejecuta como usuario normal y solicita
`sudo` solamente para paquetes o servicios del sistema. Al terminar, reinicia y
selecciona `Hyprland (uwsm-managed)` en SDDM.

Para instalar componentes concretos:

```bash
./install.sh shell nvim hyprland
./install.sh --help
```

El orden escrito no importa: el orquestador siempre respeta las dependencias.

## Módulos

| Módulo | Para qué existe |
| --- | --- |
| [`system`](components/system/README.md) | red, audio, portales, OpenVPN, SDDM y soporte de VM |
| [`themes`](components/themes/README.md) | cursor Bibata e iconos Oranchelo |
| [`fonts`](components/fonts/README.md) | JetBrainsMono Nerd Font y Lexend |
| [`shell`](components/shell/README.md) | Zsh, Starship, historial, navegación y herramientas de red |
| [`fastfetch`](components/fastfetch/README.md) | resumen visual del sistema al abrir terminal |
| [`maintenance`](components/maintenance/README.md) | revisión segura, caché de Pacman y TRIM |
| [`git-security`](components/git-security/README.md) | Git portable, identidad privada y firma SSH opcional |
| [`backup`](components/backup/README.md) | copias cifradas y verificables con Restic |
| [`workbench`](components/workbench/README.md) | entornos rootless de desarrollo y pentesting |
| [`desktop-extras`](components/desktop-extras/README.md) | Firefox, KeePassXC, Btop, grabación, color y papelera |
| [`session`](components/session/README.md) | bloqueo, inactividad, suspensión y energía |
| [`desktop-tools`](components/desktop-tools/README.md) | capturas e historial del portapapeles |
| [`files`](components/files/README.md) | Thunar, medios removibles, visores y asociaciones |
| [`hardware`](components/hardware/README.md) | Bluetooth y, en equipos físicos, firmware/SMART |
| [`security`](components/security/README.md) | keyring, agente SSH y firewall nftables |
| [`uwsm`](components/uwsm/README.md) | sesión Wayland administrada por systemd |
| [`alacritty`](components/alacritty/README.md) | terminal gráfica y registro XDG |
| [`nvim`](components/nvim/README.md) | editor LazyVim para todos los lenguajes usados |
| [`rofi`](components/rofi/README.md) | lanzador de aplicaciones |
| [`wallpaper`](components/wallpaper/README.md) | fondo administrado por Awww |
| [`hyprpanel`](components/hyprpanel/README.md) | barra, notificaciones, workspaces y estado HTB |
| [`hyprland`](components/hyprland/README.md) | compositor, ventanas, monitores y atajos |
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
| `Alt+E` | Thunar |
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
dotfiles-doctor              # comprobar toda la instalación
dotfiles-maintain check      # servicios, disco y actualizaciones
dotfiles-maintain clean      # caché segura y journal de usuario
dotfiles-backup run          # ejecutar respaldo ya configurado
dotfiles-box enter dev       # entrar al entorno de desarrollo
dotfiles-box enter pentest   # entrar al entorno Kali aislado
sysinfo                      # información visual del sistema
```

Los comandos especializados restantes están en el README de su módulo; no se
repiten aquí para mantener una referencia corta.

## Configuración privada posterior

La instalación general queda funcional, pero estas dos decisiones no deben
inventarse ni publicarse en el repositorio.

Identidad Git:

```bash
dotfiles-git-identity setup "Tu Nombre" correo@example.com
```

Para firmar commits con una llave SSH pública:

```bash
dotfiles-git-identity setup "Tu Nombre" correo@example.com ~/.ssh/id_ed25519.pub
```

Destino cifrado de respaldo:

```bash
dotfiles-backup setup /ruta/al/repositorio-restic
dotfiles-backup run
```

`backup.conf`, la contraseña de Restic, la identidad Git y `local.lua` están
ignorados por Git.

## HTB y OpenVPN

HyprPanel muestra el icono verde de HTB y la IP cuando detecta la VPN. Puedes
fijar la máquina objetivo con:

```bash
dotfiles-htb-target 10.10.11.20
dotfiles-htb-target clear
```

Ping, Nmap, HTTP y SSH hacia HTB funcionan normalmente. Solo hace falta una
regla extra cuando la máquina remota inicia una conexión nueva hacia tu
listener:

```bash
dotfiles-firewall lab-open tcp 4444
rlwrap nc -lvnp 4444
dotfiles-firewall lab-close tcp 4444
```

Ese puerto solo se expone en interfaces VPN `tun*` y desaparece al reiniciar o
recargar nftables.

## Contenedores de trabajo

Los contenedores no se crean automáticamente ni consumen espacio hasta que los
pidas:

```bash
dotfiles-box create dev
dotfiles-box create pentest
dotfiles-box list
```

Podman funciona rootless. Distrobox integra el home, pero mantiene compiladores
y herramientas específicas fuera del sistema Arch principal.

## Monitores por máquina

La base usa el modo preferido y funciona con una o varias pantallas. Para
posiciones específicas:

```bash
cp ~/.config/hypr/local.lua.example ~/.config/hypr/local.lua
hyprctl monitors all
```

Edita `local.lua` con los nombres reales; el archivo no se sube al repositorio.

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
dotfiles-doctor
git status
```
