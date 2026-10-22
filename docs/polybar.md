# Polybar

Barra X11 independiente por monitor. Awesome publica los escritorios de cada
salida y controla la visibilidad en pantalla completa. La primera barra contiene
la bandeja; las secundarias la omiten porque X11 admite un solo propietario.

```bash
./install.sh polybar
dotfiles-polybar  # recrea las barras y permanece esperando sus procesos
```

El escritorio completo aporta Awesome, fuentes, Rofi, NetworkManager, audio y
brillo. El módulo instala Polybar, BlueZ y PyGObject; la habilitación de Bluetooth
pertenece a `hardware`, que distingue equipos físicos y VMs.

## Configuración

- [`config.ini`](../config/polybar/config.ini): barras, fuentes y módulos por monitor.
- [`modules.ini`](../config/polybar/modules.ini): acciones y comandos de cada módulo.
- [`colors.ini`](../config/polybar/colors.ini): paleta.
- [`dotfiles-polybar`](../bin/dotfiles-polybar): arranque, dimensiones y controles.
- [`dotfiles-polybar-style`](../bin/dotfiles-polybar-style): tamaño por salida.

Usa JetBrainsMono e Iosevka Nerd Font instaladas por `fonts`. Los escritorios y
el indicador de micrófono siguen eventos; CPU, batería, volumen y red se consultan
según el intervalo declarado. El micrófono personal requiere `voice-isolation`;
sin ese módulo se mantiene el control básico de mute disponible.

Clic en red, Bluetooth, batería o encendido abre los menús correspondientes.
Las acciones de audio y brillo cambian el estado real al usarlas. La barra se
reinicia desde el arranque de Awesome y desde el panel de pantallas cuando procede.

## Diagnóstico

```bash
pgrep -a -x polybar
polybar --list-monitors
tail -n 60 "$XDG_RUNTIME_DIR/polybar.log"
python3 -B -m unittest discover -s tests/polybar
```

Los avisos de fuentes sustituidas indican que la familia solicitada no está
disponible. La procedencia del diseño se conserva en
[el aviso de terceros](third-party/polybar.md).

Instalador: [`setup/modules/polybar.sh`](../setup/modules/polybar.sh).
