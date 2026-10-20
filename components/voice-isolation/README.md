# Aislamiento de voz opcional

```bash
./install.sh voice-isolation
```

Instala RNNoise en el host y activa un servicio de usuario con PipeWire. La instalación normal y `all` lo excluyen. La entrada **Aislamiento de voz** se convierte en la predeterminada; las aplicaciones que tengan otro dispositivo fijado deben seleccionarla en sus ajustes.

Detecta el micrófono físico predeterminado al iniciar. Si la entrada predeterminada ya es virtual, elige el primer micrófono físico disponible. Excluye monitores de salida y fuentes virtuales para evitar realimentación. Conserva el volumen físico existente por defecto; el volumen filtrado empieza en 80%. El filtro usa detección de voz al 60%, con margen para conservar el principio y final de las palabras. Puede atenuar música y otros sonidos que no sean voz.

Los ajustes de cada equipo van en `~/.config/voice-isolation/environment`, fuera de Git. Ejemplo opcional:

```ini
VOICE_ISOLATION_INPUT_VOLUME=25%
VOICE_ISOLATION_OUTPUT_VOLUME=80%
VOICE_ISOLATION_THRESHOLD=60
# VOICE_ISOLATION_SOURCE=nombre-de-la-fuente-fisica
```

`VOICE_ISOLATION_INPUT_VOLUME=keep` conserva el nivel actual. Para elegir un micrófono concreto, consulta `pactl list short sources`; al cambiar de micrófono, reinicia el servicio. No configura el volumen de altavoces ni instala filtros en Distrobox.

```bash
systemctl --user restart dotfiles-voice-isolation.service
systemctl --user status dotfiles-voice-isolation.service
systemctl --user disable --now dotfiles-voice-isolation.service
# Tras desactivarlo, selecciona el micrófono físico en el sistema/aplicaciones.
```

La configuración generada vive en `$XDG_RUNTIME_DIR/dotfiles-voice-isolation` y no se versiona. El servicio busca primero el plugin del paquete del host; también admite la copia de usuario en `~/.local/lib/ladspa` para una instalación existente. No se incluye la biblioteca binaria en Git.

Comprobaciones sin capturar audio: `python3 components/voice-isolation/tests/test_setup.py`.
