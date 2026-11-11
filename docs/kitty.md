# Kitty

Este componente instala Kitty y lo registra como terminal gráfica de Awesome/X11.
`dotfiles-terminal` mantiene una entrada compartida para atajos, Rofi y XDG.

## Configuración

Catppuccin Mocha, opacidad 0.98, sin decoraciones ni barra de desplazamiento,
JetBrainsMono Nerd Font con las cuatro caras explícitas y Zsh de login compartido.
El cursor vertical tiene parpadeo suave y estela corta. La selección se copia al
portapapeles y Kitty recarga automáticamente su configuración. Historial de 10000
líneas y desplazamiento de tres líneas por paso de rueda.

Los atajos Ctrl+Backspace, Shift+Left/Right y Ctrl+Shift+Left/Right envían las
secuencias interpretadas por los widgets ZLE compartidos.

El tamaño base es 15 pt. El wrapper valida DOTFILES_FONT_SIZE o consulta
`dotfiles-display --font-size-at-pointer`, con valor lógico 10 por defecto, y
multiplica por 1.5. Esta equivalencia conserva las celdas de 12 × 27 píxeles medidas
en la pantalla X11 actual; otros DPI pueden requerir recalibración. Los márgenes
mínimos son 13.5 pt (18 px a 96 DPI), con los sobrantes centrados.

## Instalación y uso

```sh
./install.sh kitty
./install.sh --dry-run kitty
dotfiles-terminal
dotfiles-terminal --directory /tmp -- yazi
env DOTFILES_FONT_SIZE=9 dotfiles-terminal -- btop
```

El wrapper admite las opciones nativas de Kitty: `--class`, `--title`,
`--directory`, `--override key=value` y `--` antes del programa y sus argumentos.
No modifica ni evalúa los argumentos del programa. El valor de TERM es el nativo
`xterm-kitty`; las máquinas remotas necesitan una entrada terminfo compatible.

## Archivos e integraciones

| Destino | Responsabilidad |
| --- | --- |
| `.config/kitty/kitty.conf` | Aspecto, cursor, historial, teclado y shell. |
| `.local/bin/dotfiles-terminal` | Entrada compartida y tamaño por monitor. |
| `.local/share/applications/kitty.desktop` | Registro para menús y XDG. |
| `.config/xdg-terminals.list` | Terminal preferida. |

Alt+Enter, Ctrl+Alt+T y los menús usan el wrapper. Alt+E y el selector de archivos
usan Yazi. Btop mantiene su tamaño lógico 9. LazyDocker y respaldos conservan sus
clases especiales de Awesome.

Instalador: [kitty.sh](../setup/modules/kitty.sh). Los destinos administrados se
declaran en [links.tsv](../setup/links.tsv).

## Validación

```sh
command -v kitty dotfiles-terminal
kitty --version
python -m unittest discover -s tests/tools -p 'test_terminal.py'
```
