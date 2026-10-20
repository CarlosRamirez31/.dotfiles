# Aislamiento de voz y prueba personal

```bash
./install.sh voice-isolation
```

El aislamiento normal usa directamente RNNoise y la entrada **Aislamiento de voz**. El controlador de audio del sistema y los micrófonos físicos siguen disponibles. La instalación es opcional y se excluye de la instalación normal y de `all`.

Abre **Micrófono y aislamiento**, ejecuta `dotfiles-microphone` o usa `Alt+Shift+M` en Awesome. El panel permite elegir micrófono interno, USB, conector de audífonos o Bluetooth cuando el sistema los expone como entradas. Para Bluetooth hace falta un perfil con micrófono (HFP/HSP). Los cambios de entrada, volumen y aislamiento son acciones explícitas del panel.

En llamadas y grabación habitual elige **Aislamiento de voz** o **Predeterminado**. RNNoise trabaja a 48 kHz con detección de voz al 60%, margen de 200 ms y recuperación de 100 ms para conservar palabras. El nivel filtrado comienza en 80%; por defecto conserva la ganancia física.

## Probar Solo mi voz

La prueba es una entrada distinta: **Solo-mi-voz-experimental**. Consume el audio de RNNoise, pero no reinicia su servicio, no cambia el micrófono físico ni su ganancia y no establece una nueva entrada predeterminada. Se inicia manualmente; no se activa al instalar ni al registrar la voz. Un fallo de la prueba no detiene el aislamiento normal. Al apagarla se retiran únicamente sus módulos virtuales.

1. Mantén activo **Aislamiento de ruido**.
2. Si hace falta, pulsa **Preparar reconocimiento** y luego **Registrar mi voz (15 s)**. Habla solo tú, en un ambiente tranquilo.
3. Activa **Probar Solo mi voz · entrada separada** o ejecuta `dotfiles-microphone personal on`.
4. Selecciona **Solo-mi-voz-experimental** únicamente en la aplicación donde quieras probarla. Las demás aplicaciones pueden seguir usando **Aislamiento de voz**.
5. Para terminar, apaga la casilla o ejecuta `dotfiles-microphone personal off`. Si tu aplicación conserva un dispositivo fijo, vuelve a elegir **Aislamiento de voz**.

La detección personal usa 16 kHz y bloques de 160 ms, más el tiempo de inferencia. Puede sonar menos natural y rechazar palabras propias. Silencia bloques con probabilidad menor de 0,85; no separa voces simultáneas ni sirve para autenticar identidad. Si no alcanza tiempo real, se detiene la prueba.

**Preparar reconocimiento** instala un entorno Python privado con PyTorch CPU y [nomo-pvad release-1.1](https://github.com/tuya/nomo-pvad), fijado al commit `cb828468d183424fd574984f00b3ffbcce0be9bc`, y comprueba el modelo. RNNoise básico no descarga estos modelos. La voz se procesa localmente; el registro se descarta y solo se guarda el perfil numérico privado en `~/.local/share/voice-isolation/personal-voice/my-voice.npy`. Modelos, perfiles y ajustes particulares quedan fuera de Git.

## Actualizar desde Microfono-controlado

La instalación detiene y deshabilita el servicio del puente anterior, activa RNNoise directo y retira **Microfono-controlado**, migrando sus capturas a **Aislamiento de voz**. Conserva las entradas físicas y las capturas ajenas a ese puente. Para retirar solo la entrada vieja con RNNoise ya funcionando:

```bash
systemctl --user disable --now dotfiles-microphone.service
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

La entrada elegida y el volumen se guardan en `~/.config/voice-isolation/microphone.json`. Los ajustes de RNNoise van en `~/.config/voice-isolation/environment`:

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
