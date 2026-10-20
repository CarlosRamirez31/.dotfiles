# Aislamiento de voz y prueba personal

```bash
./install.sh voice-isolation
```

El aislamiento normal usa directamente RNNoise y la entrada **Aislamiento de voz**. El controlador de audio del sistema y los micrófonos físicos siguen disponibles. La instalación es opcional y se excluye de la instalación normal y de `all`.

Abre **Micrófono y aislamiento**, ejecuta `dotfiles-microphone` o usa `Alt+Shift+M` en Awesome. El panel permite elegir micrófono interno, USB, conector de audífonos o Bluetooth cuando el sistema los expone como entradas. Para Bluetooth hace falta un perfil con micrófono (HFP/HSP). Los cambios de entrada, volumen y aislamiento son acciones explícitas del panel.

En llamadas y grabación habitual elige **Aislamiento de voz** o **Predeterminado**. RNNoise trabaja a 48 kHz con detección de voz al 60%, margen de 200 ms y recuperación de 100 ms para conservar palabras. El nivel filtrado comienza en 80%; por defecto conserva la ganancia física.

## Probar Solo mi voz

La prueba es una entrada distinta: **Microfono-controlado-Solo-mi-voz**. Consume el audio de RNNoise, pero no reinicia su servicio, no cambia el micrófono físico ni su ganancia y no establece una nueva entrada predeterminada. Su estado y el perfil elegido se guardan automáticamente y se restauran al iniciar sesión; crear un perfil no enciende el filtro por sí solo. Un fallo de la prueba no detiene el aislamiento normal. Al apagarla se retiran únicamente sus módulos virtuales.

1. Mantén activo **Aislamiento de ruido**.
2. Pulsa **Configurar un nuevo perfil de voz…**, escribe un nombre y lee el texto propuesto. El mismo flujo prepara el reconocimiento si hace falta, cuenta tres segundos, graba 15 segundos y guarda y selecciona el perfil. Puedes crear varios perfiles y elegirlos en **Perfil de voz guardado**. El perfil anterior aparece como **Mi voz**. **Eliminar perfil** pide confirmación; si eliminas el perfil activo elige otro disponible y si era el último apaga Solo mi voz.
3. Activa **Solo mi voz · usar el perfil seleccionado** o ejecuta `dotfiles-microphone personal on`.
4. Selecciona **Microfono-controlado-Solo-mi-voz** únicamente en la aplicación donde quieras probarla. Las demás aplicaciones pueden seguir usando **Aislamiento de voz**.
5. Para terminar, apaga la casilla o ejecuta `dotfiles-microphone personal off`. Si tu aplicación conserva un dispositivo fijo, vuelve a elegir **Aislamiento de voz**.

La detección personal usa 16 kHz y bloques de 160 ms, más el tiempo de inferencia. Puede sonar menos natural y rechazar palabras propias. Abre con probabilidad de 0,60 y conserva hasta dos bloques de confianza intermedia (mínimo 0,45) para reducir palabras cortadas. Una voz claramente rechazada cierra la salida inmediatamente; no separa voces simultáneas ni sirve para autenticar identidad. Si no alcanza tiempo real, se detiene la prueba.

La preparación automática instala un entorno Python privado con PyTorch CPU y [nomo-pvad release-1.1](https://github.com/tuya/nomo-pvad), fijado al commit `cb828468d183424fd574984f00b3ffbcce0be9bc`, y comprueba el modelo. RNNoise básico no descarga estos modelos. La voz se procesa localmente; el registro se descarta y solo se guarda el perfil numérico privado en `~/.local/share/voice-isolation/personal-voice/profile-*.npy` (el perfil anterior `my-voice.npy` se conserva). Modelos, perfiles y ajustes particulares quedan fuera de Git.

## Actualizar desde Microfono-controlado

La instalación activa RNNoise directo y retira el puente obsoleto **Microfono-controlado**, migrando sus capturas a **Aislamiento de voz**. Restaura el filtro personal si estaba guardado como encendido. Conserva las entradas físicas y las capturas ajenas a ese puente. Para retirar solo la entrada vieja con RNNoise ya funcionando:

```bash
dotfiles-microphone personal off
systemctl --user daemon-reload
dotfiles-microphone cleanup-legacy
```

No hace falta reiniciar RNNoise para cargar el nuevo programa del panel; si estaba abierto, ciérralo y vuelve a abrirlo.

## Controles

Polybar indica qué aplicaciones capturan audio. Clic izquierdo abre el menú compacto; clic derecho alterna el silencio global. Las casillas por aplicación silencian los flujos actuales, sin revocar permisos permanentes. `Alt+Ctrl+M` alterna el silencio global, `Alt+Ctrl+N` el aislamiento normal y `Alt+Ctrl+V` la prueba personal. Apagar RNNoise detiene también la prueba, que depende de él.

```bash
dotfiles-microphone list
dotfiles-microphone compact
dotfiles-microphone off
dotfiles-microphone on
dotfiles-microphone noise on
dotfiles-microphone personal on
dotfiles-microphone personal off
dotfiles-microphone source NOMBRE_FUENTE [NOMBRE_CONECTOR]
```

El panel confirma los cambios guardados y muestra si reconoce la voz del perfil o está esperando. La activación comprueba que el servicio recibe audio antes de confirmar. La entrada elegida, el volumen, los nombres de perfiles y la selección se guardan en `~/.config/voice-isolation/microphone.json`. Los ajustes de RNNoise van en `~/.config/voice-isolation/environment`:

```ini
VOICE_ISOLATION_INPUT_VOLUME=keep
VOICE_ISOLATION_OUTPUT_VOLUME=80%
VOICE_ISOLATION_THRESHOLD=60
# VOICE_ISOLATION_SOURCE=nombre-de-la-fuente-fisica
```

La configuración generada vive en `$XDG_RUNTIME_DIR/dotfiles-voice-isolation`. El plugin se busca en el host y, como alternativa, en `~/.local/lib/ladspa`. No se instalan filtros en Distrobox ni se cambia el volumen de los altavoces.

Comprobaciones sin capturar audio:

```bash
python3 -m unittest discover -s components/voice-isolation/tests
```

El servicio y sus comandos se ejecutan en el host. Apagar Solo mi voz guarda `personal: false` y detiene el proceso sin eliminar el enlace de su unidad de systemd. Si el enlace falta por una desactivación anterior, el panel lo restaura desde el componente instalado al encender el filtro.

Solo mi voz solicita búferes de captura y reproducción de 20 ms, sin búfer adicional de Python. El modelo analiza bloques de 160 ms, por lo que conserva una latencia propia; el estado muestra el tiempo de procesamiento para diagnosticar carga de CPU. La tolerancia breve a menor confianza mejora la continuidad a cambio de una menor rigidez al filtrar voces.
