# Dotfiles

**Autor: Carlos Ramirez · © 2026 · [Licencia MIT](LICENSE)**

Escritorio Arch Linux reproducible para programación, uso diario y laboratorios
de seguridad autorizados. El conjunto usa AwesomeWM sobre X11, Alacritty, Zsh y
Neovim con una apariencia coherente y módulos instalables por separado.

La configuración prioriza cuatro ideas:

- instalar solamente lo que cada módulo necesita;
- no reinstalar paquetes que ya existen;
- respaldar archivos ajenos antes de enlazar los administrados;
- mantener identidades, contraseñas y ajustes por máquina fuera de Git.

## Dónde está cada cosa

```text
config/        Configuración de aplicaciones → ~/.config/
home/          Archivos como .zshrc y .xprofile → ~/
bin/           Comandos personales → ~/.local/bin/
libexec/       Programas auxiliares → ~/.local/libexec/
share/         Lanzadores y recursos → ~/.local/share/
system/        Servicios systemd y tema de SDDM
assets/        Fondos y fuentes
environments/  Workbench/Podman y Hermes
setup/         Instaladores, biblioteca y mapa de enlaces
tests/         Pruebas agrupadas por módulo
docs/          Guías de uso
```

`setup/links.tsv` declara el módulo propietario, el archivo fuente y su destino.
Los destinos instalados se conservan aunque cambie la organización del repositorio.
Consulta [la organización y los enlaces](docs/estructura.md) para localizar las fuentes y sus destinos.

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

Hermes y el escritorio virtual se activan únicamente de forma explícita:

```bash
./install.sh hermes
./install.sh all hermes
./install.sh --dry-run all
```

`./install.sh` y `./install.sh all` no instalan ni configuran Hermes. Consulta el
[componente opcional](environments/hermes/README.md) para autenticación y capturas.

Flutter con Android SDK, emulador y dispositivo virtual en `dev` también es opcional:

```bash
./install.sh flutter
./install.sh all flutter
```

Solo se activa al escribir `flutter`; la instalación normal y `all` lo excluyen.
Consulta el [componente Flutter](docs/flutter.md).

Rider para C# también es opcional y se instala únicamente dentro de `dev`:

```bash
./install.sh rider
rider .                    # abrir la carpeta actual en Rider dentro de dev
```

La instalación normal y `all` lo excluyen. Consulta el [componente Rider](docs/rider.md).

Docker CLI/Compose y DBeaver también son opcionales dentro de `dev`:

```bash
./install.sh docker dbeaver
```

El cliente Docker usa por defecto la API compatible del Podman rootless existente. LazyDocker es general del entorno: `lazydocker` funciona desde el host y dentro de `dev-podman`, `Alt+Shift+D` abre una ventana centrada y `Space+gk` hace lo mismo dentro de Neovim.

El orden escrito no importa: el orquestador usa un orden fijo de instalación.
La selección parcial no añade dependencias entre módulos automáticamente; instala
primero la base completa para usar los componentes del escritorio por separado.
Los opcionales de desarrollo requieren un `dev-podman` ya preparado;
`./install.sh workbench` instala el proveedor, pero no crea ese contenedor.

El aislamiento de voz con RNNoise es opcional y funciona en el host para aplicaciones de llamadas y grabación:

```bash
./install.sh voice-isolation
```

Detecta el micrófono de cada equipo y mantiene sus ajustes locales fuera de Git. Consulta [Aislamiento de voz](docs/voice-isolation.md).

## Contenedores de trabajo

Los comandos de acceso son `dev-podman`, `parrotos-podman` y `kali-podman`. Sin argumentos entran al entorno correspondiente; también aceptan acciones:

```bash
dev-podman enter
parrotos-podman enter
kali-podman enter

# Cambia el nombre para administrar cualquiera de los tres entornos.
dev-podman start
dev-podman ps
dev-podman stop
dev-podman restart
```

`rm` elimina el contenedor detenido; admite `--force` y `--volumes`. Los documentos enlazados permanecen en el host. La [guía de Podman](environments/workbench/podman/README.md) explica, en orden, cómo crear, configurar, entrar, consultar todos los servicios, detener, borrar y reconstruir los tres perfiles, con sus comandos nativos equivalentes.

## Módulos

| Módulo | Para qué existe |
| --- | --- |
| [`system`](docs/system.md) | red, audio, portal GTK/X11, OpenVPN, SDDM y soporte de VM |
| [`sddm`](docs/sddm.md) | tema SilentSDDM con Catppuccin Mocha y teclado virtual en la pantalla de inicio |
| [`themes`](docs/themes.md) | cursor Bibata e iconos Oranchelo |
| [`fonts`](docs/fonts.md) | JetBrainsMono, Iosevka Nerd Font, Lexend e iconos/emoji |
| [`shell`](docs/shell.md) | Zsh, Starship, historial, navegación y herramientas de red |
| [`fastfetch`](docs/fastfetch.md) | resumen visual del sistema al abrir terminal |
| [`maintenance`](docs/maintenance.md) | revisión segura, caché de Pacman y TRIM |
| [`quality`](docs/quality.md) | validación de fuentes, datos, documentación y pruebas |
| [`git-security`](docs/git-security.md) | Git portable, identidad privada y firma SSH opcional |
| [`backup`](docs/backup.md) | copias cifradas y verificables con Restic |
| [`hermes`](environments/hermes/README.md) **opcional** | Hermes en dev, skills académicas y escritorio virtual con capturas del host |
| [`flutter`](docs/flutter.md) **opcional** | Flutter estable, Android SDK, emulador sin marco y AVD en dev |
| [`rider`](docs/rider.md) **opcional** | JetBrains Rider y SDK .NET en dev; `rider .` abre la carpeta actual |
| [`docker`](docs/docker.md) **opcional** | Docker CLI, Compose y Buildx en dev, usando la API compatible de Podman |
| [`dbeaver`](docs/dbeaver.md) **opcional** | DBeaver Community en dev, con lanzador gráfico independiente |
| [`voice-isolation`](docs/voice-isolation.md) **opcional** | Aislamiento de voz RNNoise con detección del micrófono y arranque automático |
| [`workbench`](environments/workbench/README.md) | entornos rootless de desarrollo y pentesting |
| [`desktop-extras`](docs/desktop-extras.md) | Firefox, KeePassXC, Btop, color y papelera |
| [`session`](docs/session.md) | bloqueo, inactividad, suspensión y energía |
| [`desktop-tools`](docs/desktop-tools.md) | capturas e historial del portapapeles |
| [`files`](docs/files.md) | Yazi, selector del sistema, Thunar, visores y asociaciones |
| [`hardware`](docs/hardware.md) | Bluetooth y, en equipos físicos, firmware/SMART |
| [`security`](docs/security.md) | keyring, agente SSH y firewall nftables |
| [`alacritty`](docs/alacritty.md) | terminal gráfica y registro XDG |
| [`nvim`](docs/nvim.md) | editor LazyVim para todos los lenguajes usados |
| [`rofi`](docs/rofi.md) | lanzador de aplicaciones |
| [`wallpaper`](docs/wallpaper.md) | carrusel GTK/X11 y fondo Feh |
| [`awesome`](docs/awesome.md) | sesión X11, ventanas, notificaciones y Picom |
| [`polybar`](docs/polybar.md) | barra por monitor, escritorios, audio, red y batería |
| [`doctor`](docs/doctor.md) | diagnóstico final de toda la instalación |

Cada guía enlazada explica sus archivos, decisiones y los pocos comandos que
realmente forman parte de su uso.

## Gramática del teclado

La tecla principal es `Alt`. `Super+P` abre pantallas y `Super+Space` cambia
el teclado; en una VM esas dos combinaciones pueden ser capturadas por el anfitrión.
Consulta [todos los atajos](docs/awesome-atajos.md).

| Atajo | Acción |
| --- | --- |
| `Alt+H/J/K/L` | enfocar izquierda/abajo/arriba/derecha |
| `Alt+Shift+H/J/K/L` | mover ventana |
| `Alt+Ctrl+H/J/K/L` | redimensionar ventana |
| `Alt+1..4` | cambiar entre los cuatro workspaces |
| `Alt+Shift+1..4` | mover ventana al workspace |
| `Alt+Q` | cerrar ventana |
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
| `Super+Space` | alternar teclado US / Español Latinoamericano |
| `Alt+C` | historial del portapapeles |
| `Ctrl+Shift+B` | bloquear |
| `Alt+Shift+E` | cerrar sesión |

Captura y utilidades:

| Atajo | Acción |
| --- | --- |
| `Print` | capturar pantalla completa |
| `Alt+Print` | capturar región |
| `Alt+Shift+S` | capturar región |
| `Alt+Shift+C` | copiar color de la pantalla |

Las teclas físicas controlan volumen, micrófono, brillo y reproducción incluso
con la pantalla bloqueada.

## Comandos cotidianos

```bash
doctor                       # diagnóstico del escritorio instalado
maintain check               # servicios, disco y actualizaciones
maintain clean               # caché segura y journal de usuario
backup run                   # ejecutar respaldo ya configurado
dev-podman                   # entrar al entorno de desarrollo
kali-podman                  # entrar al entorno Kali
parrotos-podman              # entrar al entorno Parrot, si fue creado
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

`backup.conf` y la identidad Git privada están ignorados por Git; los ajustes
de monitores y micrófono se guardan en el home, fuera de las fuentes versionadas.
El respaldo semanal abre una terminal flotante. La contraseña se introduce allí y no se guarda en un archivo.

## HTB y OpenVPN

Polybar muestra el icono verde de HTB y la IP cuando detecta la VPN. Puedes
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

## Crear entornos

`./install.sh workbench` prepara Podman y sus utilidades. Los contenedores se
crean solo cuando lo pides:

```bash
dev-podman setup --fresh
parrotos-podman setup
kali-podman setup
```

La receta `dev --fresh` instala la pila completa de desarrollo, incluidos los
cinco componentes Docker, DBeaver, Rider, Flutter y Hermes. Requiere una terminal
para revisar las licencias de Android. Esta receta es distinta de `./install.sh all`,
que no selecciona esos componentes opcionales.

Cada contenedor tiene home privado y acceso al home real mediante `/host-home`.
Los perfiles Distrobox anteriores quedan documentados en
[Workbench](environments/workbench/README.md); ya no son la ruta de desarrollo.

## Monitores

Awesome usa la salida disponible y su modo preferido. Consulta las salidas y
modos reales antes de cambiar resolución o posición:

```bash
xrandr --query
xrandr --output NOMBRE_REAL --mode 1920x1080 --rate 60
```

Sustituye `NOMBRE_REAL` por el nombre reportado por XRandR; no copies ese ajuste
a un equipo con salidas distintas.

## Mantenimiento del repositorio

Los paquetes existentes se omiten mediante `pacman -Q` y `pacman --needed`.
El instalador crea enlaces por archivo según `setup/links.tsv`; si encuentra
un archivo ajeno, lo respalda con un sufijo `.backup.FECHA-HORA.PID`. Las configuraciones locales y secretos nunca
se reemplazan deliberadamente.

Después de cualquier cambio importante:

```bash
./check.sh
doctor
git status
```

## Licencia y atribuciones

El trabajo original de Carlos Ramirez en este repositorio se publica bajo la
[licencia MIT](LICENSE): permite usar, modificar y redistribuir ese material,
incluido su uso comercial, conservando el aviso de copyright y la licencia.

Los componentes de terceros y las adaptaciones sujetas a sus licencias conservan
sus condiciones y atribuciones; la licencia MIT del proyecto no las sustituye:

- [Configuración de Neovim: Apache-2.0](config/nvim/LICENSE).
- [Tema SilentSDDM: procedencia y GPL-3.0-or-later](system/sddm/theme/UPSTREAM.md).
- [Fuentes Lexend: SIL OFL](assets/fonts/Lexend/OFL.txt).
- [Fuentes del tema SDDM: SIL OFL](system/sddm/theme/fonts/OFL.txt).
- [Diseño adaptado de Awesome: GPL-3.0-or-later](docs/third-party/awesome.md).
- [Diseño adaptado de Polybar: MIT y atribución a ZProger](docs/third-party/polybar.md).
