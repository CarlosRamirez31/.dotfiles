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

Las cápsulas de escritorios y hora combinan un fondo rectangular con los
semicírculos `` y ``. Los extremos usan Iosevka Regular a 17 pt con
desplazamiento vertical 4 para una barra de 30 px a 96 DPI. El script de estilo
escala esas medidas por monitor. Cambiar solamente la fuente o su desplazamiento
puede dejar el fondo sobresaliendo como un cuadrado o recortar la curva.

Clic en red, Bluetooth, batería o encendido abre los menús correspondientes.
Las acciones de audio y brillo cambian el estado real al usarlas. La barra se
reinicia desde el arranque de Awesome y desde el panel de pantallas cuando procede.

El icono de Arch abre el panel del sistema (usuario, tiempo activo, CPU, RAM,
disco y accesos a conexiones y sesión). El clic derecho conserva el lanzador
de aplicaciones. El botón de música después de los escritorios abre el panel
ligero de Awesome con portada de fondo, progreso morado, controles de reproducción
y una tarjeta con la pista actual a la derecha. Controla por MPRIS el reproductor
activo, incluido Limusic, sin abrir su ventana ni su Mini Player. La cola de Limusic
no está disponible por MPRIS: el panel muestra únicamente información real de la
pista actual. Ambos paneles cierran con la X o un segundo clic en su icono y
permiten seguir usando las aplicaciones y los atajos del escritorio.

El panel incluye interruptores directos de red, Bluetooth, modo avión y luz
nocturna. El icono de red distingue Ethernet y Wi-Fi según la conexión activa;
en Wi-Fi enciende/apaga la radio y en Ethernet desconecta/reconecta el dispositivo.
Modo avión bloquea las radios con rfkill y al salir restaura cuáles estaban
habilitadas. Luz nocturna aplica una gamma cálida a las pantallas activas y
restaura su gamma anterior al apagarla. La terminal conserva su acceso directo.
Limusic se instala desde AUR con el módulo `desktop-extras`, incluido en la
instalación completa. El panel guarda las portadas con un límite de 5 MiB y 64 imágenes en `$XDG_CACHE_HOME/dotfiles/music`.
El clima se obtiene de wttr.in, se guarda durante 20 minutos y usa Santo Domingo
por defecto. `DOTFILES_WEATHER_CITY` permite cambiar la ciudad en la sesión.
El contador de actualizaciones usa la base local de pacman; no sincroniza
repositorios. El avatar usa `~/.face` si existe y el icono de Arch en su ausencia.

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
