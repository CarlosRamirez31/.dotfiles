# Dotfiles

Escritorio Hyprland mínimo y reproducible para Arch Linux. Cada programa tiene
su configuración y su instalador independiente; el instalador raíz solamente
los orquesta en un orden seguro.

## Instalación completa

```bash
git clone https://github.com/CarlosRamirez31/.dotfiles.git ~/.dotfiles
cd ~/.dotfiles
./install.sh
```

El orden de la instalación completa es:

1. `system`: servicios base, audio, red y soporte de la máquina virtual.
2. `themes`: cursor Bibata e iconos Oranchelo.
3. `fonts`: Lexend para el panel y JetBrainsMono Nerd Font para la terminal.
4. `shell`: Zsh, Oh My Zsh, Starship, historial y herramientas de terminal.
5. `fastfetch`: tarjeta visual con la información importante del sistema.
6. `session`: bloqueo, inactividad, pantalla y energía segura.
7. `desktop-tools`: capturas, editor, portapapeles y teclas multimedia.
8. `files`: Thunar, USB/MTP, miniaturas y aplicaciones predeterminadas.
9. `hardware`: Bluetooth y Blueman.
10. `security`: keyring, agente SSH y firewall para estación de trabajo/lab.
11. `uwsm`: variables de la sesión Wayland.
12. `alacritty`: terminal y su configuración visual.
13. `nvim`: Neovim, LazyVim, herramientas de desarrollo y plugins bloqueados.
14. `rofi`: lanzador de aplicaciones y su script auxiliar.
15. `wallpaper`: fondo y `awww`.
16. `hyprpanel`: barra, menús y notificaciones.
17. `hyprland`: compositor, atajos, reglas y tema de ventanas.
18. `doctor`: validación final de comandos, enlaces, servicios y Hyprland.

Los paquetes ya instalados se omiten mediante `pacman -Q` y `pacman --needed`.
Los archivos existentes que no pertenecen a este repositorio se renombran con
el sufijo `.backup.FECHA-HORA` antes de crear los enlaces administrados.

## Instalar solo una parte

Cada módulo funciona directamente:

```bash
./components/alacritty/install.sh
./components/shell/install.sh
./components/hyprland/install.sh
./components/nvim/install.sh
```

También se pueden pedir varios al orquestador. El orden escrito no importa: el
script siempre los reordena según sus dependencias.

```bash
./install.sh hyprland alacritty rofi
```

Para ver los nombres disponibles:

```bash
./install.sh --help
```

## Estructura

```text
components/
  alacritty/   # ~/.config/alacritty
  fastfetch/   # tarjeta de información del sistema
  session/     # bloqueo, idle y suspensión segura
  desktop-tools/ # capturas y portapapeles
  files/       # gestor de archivos y asociaciones
  hardware/    # Bluetooth
  security/    # credenciales y firewall
  doctor/      # diagnóstico final
  fonts/       # ~/.local/share/fonts
  hyprland/    # ~/.config/hypr
  hyprpanel/   # plantilla copiada al directorio de ejecución
  nvim/        # configuración LazyVim importada y portable
  rofi/        # ~/.config/rofi y lanzador
  shell/       # Zsh, Starship, aliases y herramientas interactivas
  system/      # paquetes y servicios del sistema
  themes/      # temas instalados desde AUR
  uwsm/        # ~/.config/uwsm
  wallpaper/   # ~/.config/wallpapers
scripts/
  lib.sh       # funciones compartidas por los instaladores
install.sh     # orquestador
```

## Terminal y shell

El componente `shell` instala Zsh con Oh My Zsh y un prompt Starship de dos
líneas basado en Tokyo Night. Incluye iconos y estado Git, usuario/equipo,
directorio, duración, hora y código de salida. `eza`, `vivid` y `bat` mejoran la
vista de directorios y archivos; `fzf` permite buscar el historial con
`Ctrl+R`, archivos con `Ctrl+T` y directorios con `Alt+C`; `zoxide` aprende las
rutas frecuentes mediante `z` y `zi`.

También se instalan sugerencias mientras se escribe, resaltado de sintaxis,
completado adicional, historial compartido de 100 000 entradas y utilidades
generales para programación, redes y pruebas autorizadas. Puede instalarse de
forma independiente con `./install.sh shell` o como parte de `./install.sh`.
Alacritty abre `/usr/bin/zsh` explícitamente para que una sesión gráfica antigua
no siga reutilizando el valor anterior de `SHELL`.

La apariencia se cambia principalmente en `components/shell/dotfiles/.config/starship.toml`.
Los alias están en `.config/zsh/aliases.zsh` y las funciones propias en
`.config/zsh/functions.zsh`. Al terminar la instalación hay que abrir una
terminal nueva para que el cambio de shell tenga efecto.

Alacritty y el prompt conservan `JetBrainsMono Nerd Font`, la fuente actual de
la terminal. El componente `fonts` también instala su paquete para que los
iconos se vean correctamente en una instalación nueva.

## Información del sistema

`fastfetch` reemplaza a Neofetch con una tarjeta más rápida y mantenida. Se
muestra automáticamente al abrir una terminal Zsh e incluye el logo completo
de Arch, sistema, kernel, Hyprland, terminal y fuente, CPU/GPU, memoria, disco,
IP local y batería cuando está disponible. También puede ejecutarse con
`fastfetch` o `sysinfo`, e instalarse por separado con `./install.sh fastfetch`.

Su aspecto y módulos se cambian en
`components/fastfetch/dotfiles/.config/fastfetch/config.jsonc`. Para ocultarlo
al iniciar Zsh sin desinstalarlo, define `DOTFILES_FASTFETCH=0`.

La configuración de Neovim se importó desde
`CarlosRamirez31/nvim-config` sin su historial Git anidado, por lo que ahora
forma parte del historial único de este repositorio. En Arch se instala con el
`install.sh` general. En Windows, desde PowerShell:

```powershell
.\components\nvim\install.ps1
```

El arranque instala parsers de Tree-sitter para C#, Python, Rust, Dart/Flutter,
Lua, JavaScript, TypeScript/TSX (React Native) y formatos generales de web,
shell, bases de datos, Git, configuración y documentación.

Flutter detecta el Android SDK mediante `ANDROID_SDK_ROOT`, `ANDROID_HOME` o
las rutas estándar de Windows, Linux y macOS; ya no contiene un nombre de
usuario fijo.

Alacritty es el terminal predeterminado para `Ctrl+Alt+T`, `Super+Enter` y el
clic central del panel. Se abre sin barra de título ni decoración del sistema,
con el mismo estilo limpio de la configuración anterior.

Después de una instalación limpia, reinicia y selecciona
`Hyprland (uwsm-managed)` en la pantalla de inicio.

## Escritorio diario y atajos

La sesión se bloquea con `Super+L` y automáticamente tras diez minutos. La
pantalla se apaga un minuto después y el equipo físico puede suspenderse a los
30 minutos; las máquinas virtuales y los equipos con una conexión SSH entrante
activa no se suspenden. `Super+E` abre Thunar.

- `Print`: captura la pantalla completa.
- `Super+Print`: selecciona un área.
- `Super+Shift+S`: selecciona un área y la abre en Swappy.
- `Super+C`: busca el historial del portapapeles con Rofi.
- `Super+L`: bloquea inmediatamente con Hyprlock.

Los monitores usan una regla portable. Para una máquina concreta copia
`~/.config/hypr/local.lua.example` como `~/.config/hypr/local.lua` y agrega las
salidas indicadas por `hyprctl monitors all`; ese archivo queda fuera de Git.

## Seguridad y laboratorios

GNOME Keyring guarda secretos y proporciona el agente SSH. El firewall bloquea
conexiones entrantes no solicitadas, pero permite respuestas, DHCP e ICMP. Para
un listener de un laboratorio autorizado abre temporalmente un puerto solo en
interfaces VPN `tun*`:

```bash
dotfiles-firewall lab-open tcp 4444
dotfiles-firewall lab-close tcp 4444
dotfiles-firewall status
```

Esos puertos se cierran al reiniciar o recargar el firewall. Si la instalación
general se ejecuta mediante SSH, el firewall se instala pero no se activa para
evitar cortar la sesión; se activa localmente con
`dotfiles-firewall enable`. Ejecuta `dotfiles-doctor` cuando quieras revisar el
estado completo del escritorio.
