# Aislamiento de voz opcional

```bash
./install.sh voice-isolation
```

Instala RNNoise en el host y activa servicios de usuario con PipeWire. La instalación normal y `all` lo excluyen. Abre **Micrófono y aislamiento** en el lanzador, ejecuta `dotfiles-microphone` o usa `Alt+Shift+M` en Awesome. El panel muestra el micrófono y el conector que realmente utiliza el procesador. Permite elegir entradas internas, USB, conector de audífonos y Bluetooth cuando el sistema las expone como fuentes de grabación.

En OBS y otras aplicaciones selecciona **Microfono-controlado** o **Predeterminado**. La entrada mantiene el mismo nombre al cambiar de micrófono o filtros. Las aplicaciones con un dispositivo físico fijado deben cambiarlo una vez en sus ajustes. El micrófono original sigue disponible.

Polybar muestra un icono y el nombre de las aplicaciones que capturan el micrófono en todas las pantallas. Excluye la captura del audio del escritorio y los procesos internos de los filtros. Clic izquierdo abre un menú compacto con entrada, volumen, filtros y capturas por aplicación; clic derecho alterna el silencio global. Las casillas por aplicación silencian o reactivan sus flujos actuales de grabación; no revocan permisos permanentes ni impiden que la aplicación cree otro flujo después. Con el micrófono global silenciado, el icono permanece visible aunque no haya aplicaciones capturando.

El menú completo también aparece como **Micrófono y aislamiento** en aplicaciones. `Alt+Shift+M` abre la configuración completa; `Alt+Ctrl+M` y la tecla de silenciar micrófono alternan el silencio global. La desactivación silencia tanto las entradas físicas como las procesadas. El volumen elegido en el panel se guarda por micrófono/conector y se restablece si una aplicación intenta subirlo.

Las casillas muestran su atajo de teclado en tono tenue: `Alt+Ctrl+M` para el micrófono, `Alt+Ctrl+N` para el aislamiento de ruido y `Alt+Ctrl+V` para Solo mi voz (requiere perfil registrado).

Los interruptores son independientes: **Aislamiento de ruido** activa RNNoise; **Solo mi voz** activa la detección personal experimental. Se pueden usar juntos, por separado o desactivar ambos. Sin detección personal, el puente trabaja a 48 kHz; con ella, utiliza 16 kHz y bloques de 160 ms, más el tiempo de inferencia. Solo deja pasar bloques con probabilidad de coincidencia igual o mayor a 0,85; silencia por completo los demás, sin prolongar la apertura después de un bloque rechazado. **No separa voces simultáneas** y puede aceptar o rechazar voces por error, especialmente con micrófonos o distancias distintos. No garantiza que ninguna otra voz pase.

### Elegir audífonos

Conecta los audífonos y pulsa **Actualizar micrófonos / audífonos conectados**. Elige su entrada en la lista. Para Bluetooth el sistema debe ofrecer un perfil con micrófono (HFP/HSP); un dispositivo que solo exponga reproducción no aparece en el selector. Los conectores analógicos disponibles aparecen por separado. Si una entrada seleccionada desaparece, el servicio avisa y espera una nueva selección, en vez de cambiar intencionadamente a otro micrófono.

### Registrar tu voz

**Preparar reconocimiento** instala un entorno Python privado con PyTorch CPU y [nomo-pvad release-1.1](https://github.com/tuya/nomo-pvad), fijado al commit `cb828468d183424fd574984f00b3ffbcce0be9bc`. Descarga el modelo y su backbone ERes2NetV2; comprueba que distingue las muestras proporcionadas y que la inferencia alcanza tiempo real. La instalación básica de RNNoise no descarga estos modelos.

Después pulsa **Registrar mi voz (15 s)** y habla solo tú, con voz normal, en un ambiente tranquilo. La grabación se procesa en memoria y se descarta; solo se conserva el perfil numérico en `~/.local/share/voice-isolation/personal-voice/my-voice.npy`, con permisos privados. Se activa **Solo mi voz** únicamente después del registro. Si cambias mucho de micrófono o entorno, puede ser necesario repetirlo. Este filtro no sirve para autenticar identidad.

El reconocimiento se ejecuta localmente. Los modelos se descargan al prepararlo; la voz no se envía a servicios externos. Los perfiles, modelos y ajustes particulares no van en Git.

```bash
dotfiles-microphone list
dotfiles-microphone status
dotfiles-microphone compact        # menú pequeño centrado
dotfiles-microphone off            # apagar / silenciar
dotfiles-microphone on             # encender / reactivar
dotfiles-microphone toggle         # alternar
dotfiles-microphone noise on       # u off
dotfiles-microphone personal on    # u off; requiere registro previo
dotfiles-microphone source NOMBRE_FUENTE [NOMBRE_CONECTOR]
```

Sin una selección guardada, detecta el micrófono físico predeterminado al iniciar; si la entrada predeterminada ya es virtual, elige el primero disponible. Excluye monitores de salida y fuentes virtuales para evitar realimentación. Cada micrófono conserva su volumen físico. El filtro RNNoise usa detección de voz al 60%, con margen para conservar el principio y final de las palabras. Puede atenuar música y otros sonidos que no sean voz.

Los ajustes de cada equipo van en `~/.config/voice-isolation/environment`, fuera de Git. Ejemplo opcional:

```ini
VOICE_ISOLATION_INPUT_VOLUME=25%
VOICE_ISOLATION_OUTPUT_VOLUME=80%
VOICE_ISOLATION_THRESHOLD=60
# VOICE_ISOLATION_SOURCE=nombre-de-la-fuente-fisica
```

`VOICE_ISOLATION_INPUT_VOLUME=keep` conserva el nivel actual. El panel mantiene este valor al cambiar de entrada para no imponer la ganancia de la laptop a los audífonos. La selección y los interruptores se guardan en `~/.config/voice-isolation/microphone.json`. No configura el volumen de altavoces ni instala filtros en Distrobox.

```bash
systemctl --user restart dotfiles-microphone.service
systemctl --user status dotfiles-microphone.service
systemctl --user disable --now dotfiles-microphone.service dotfiles-voice-isolation.service
# Tras desactivarlo, selecciona el micrófono físico en el sistema/aplicaciones.
```

La configuración generada vive en `$XDG_RUNTIME_DIR/dotfiles-voice-isolation` y no se versiona. El servicio busca primero el plugin del paquete del host; también admite la copia de usuario en `~/.local/lib/ladspa` para una instalación existente. No se incluye la biblioteca binaria en Git.

Comprobaciones sin capturar audio: `python3 -m unittest discover -s components/voice-isolation/tests`.
