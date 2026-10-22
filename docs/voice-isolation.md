# Aislamiento de voz y prueba personal

```bash
./install.sh voice-isolation
```

El aislamiento normal usa directamente RNNoise y la entrada **Aislamiento de voz**. El controlador de audio del sistema y los micrófonos físicos siguen disponibles. La instalación es opcional y se excluye de la instalación normal y de `all`.

Abre **Micrófono y aislamiento**, ejecuta `dotfiles-microphone` o usa `Alt+Shift+M` en Awesome. El panel permite elegir micrófono interno, USB, conector de audífonos o Bluetooth cuando el sistema los expone como entradas. Para Bluetooth hace falta un perfil con micrófono (HFP/HSP). Los cambios de entrada, volumen y aislamiento son acciones explícitas del panel.

En llamadas y grabación habitual elige **Aislamiento de voz** o **Predeterminado**. RNNoise trabaja a 48 kHz con detección de voz al 60%, margen de 200 ms y recuperación de 100 ms para conservar palabras. El nivel filtrado comienza en 80%; por defecto conserva la ganancia física.

## Probar Solo mi voz

La prueba es una entrada distinta: **Microfono solo mi voz**. Los perfiles nuevos reconocen sobre audio original y usan RNNoise para limpiar la salida; los anteriores conservan su reconocimiento sobre RNNoise. La prueba no reinicia el servicio de ruido, no cambia el micrófono físico ni su ganancia y no establece una nueva entrada predeterminada. Su estado y el perfil elegido se guardan automáticamente y se restauran al iniciar sesión; crear un perfil no enciende el filtro por sí solo. Al habilitar Solo mi voz, un supervisor ligero mantiene su entrada disponible. El modelo se carga únicamente cuando una aplicación captura desde esa entrada, y se cierra al terminar o silenciar la captura, al cambiar a otro micrófono o al silenciar el micrófono globalmente. Los dispositivos físicos y RNNoise siguen disponibles. La primera captura necesita un breve tiempo de carga; el panel indica cuándo está cargando, listo o reconociendo. Un fallo de la prueba no detiene el aislamiento normal. Al apagar la opción Solo mi voz explícitamente se retiran únicamente sus módulos virtuales. Mientras la opción está habilitada, su entrada permanece visible incluso sin modelo en ejecución.

1. Mantén activo **Aislamiento de ruido**.
2. Pulsa **Configurar un nuevo perfil de voz…**, escribe un nombre y lee el texto propuesto. El mismo flujo prepara el reconocimiento si hace falta, cuenta tres segundos, graba 15 segundos y guarda y selecciona el perfil. Puedes crear varios perfiles y elegirlos en **Perfil de voz guardado**. El perfil anterior aparece como **Mi voz**. **Eliminar perfil** pide confirmación; si eliminas el perfil activo elige otro disponible y si era el último apaga Solo mi voz.
3. Activa **Solo mi voz · usar el perfil seleccionado** o ejecuta `dotfiles-microphone personal on`.
4. Selecciona **Microfono solo mi voz** únicamente en la aplicación donde quieras probarla. Las demás aplicaciones pueden seguir usando **Aislamiento de voz**.
5. Para terminar, apaga la casilla o ejecuta `dotfiles-microphone personal off`. Si tu aplicación conserva un dispositivo fijo, vuelve a elegir **Aislamiento de voz**.

La detección personal usa 16 kHz y bloques de 160 ms, más el tiempo de inferencia. Puede sonar menos natural y rechazar palabras propias. Conserva los umbrales originales: abre con probabilidad de 0,60 y mantiene hasta tres bloques de confianza intermedia (mínimo 0,45), un margen de 480 ms para reducir palabras cortadas. Cada bloque reconocido renueva ese margen. Una probabilidad inferior a 0,45 cierra la salida inmediatamente, incluso si acababa de reconocer el perfil; después necesita alcanzar 0,60 para volver a abrir. No separa voces simultáneas ni sirve para autenticar identidad. Si no alcanza tiempo real, se detiene la prueba.

La preparación automática instala un entorno Python privado con PyTorch CPU y [nomo-pvad release-1.1](https://github.com/tuya/nomo-pvad), fijado al commit `cb828468d183424fd574984f00b3ffbcce0be9bc`, y comprueba el modelo. RNNoise básico no descarga estos modelos. La voz se procesa localmente; el registro se descarta y solo se guarda el perfil numérico privado en `~/.local/share/voice-isolation/personal-voice/profile-*.npy` (el perfil anterior `my-voice.npy` se conserva). Modelos, perfiles y ajustes particulares quedan fuera de Git.

## Volumen de entrada

Si la voz se vuelve metálica, distorsionada o inestable, revisa primero el volumen de entrada del micrófono físico. En la comprobación local, reducirlo manualmente resolvió el problema audible. Conserva ese nivel durante el uso y las comparaciones; los contadores de salida sin recorte no descartan una entrada demasiado alta.

## Selector de micrófonos de Firefox

Las entradas `Monitor of …` capturan salidas de audio; no son micrófonos adicionales. El estilo `share/voice-isolation/firefox-microphones.css` oculta esas filas únicamente en el diálogo de permiso de micrófono de Firefox, sin retirar dispositivos de PipeWire. Para usarlo, copia el archivo a `chrome/voice-isolation-microphones.css` dentro del perfil de Firefox, importa `@import url("voice-isolation-microphones.css");` al inicio de `chrome/userChrome.css` y activa `toolkit.legacyUserProfileCustomizations.stylesheets` en `user.js`. Reinicia Firefox. Los selectores internos de páginas y otras aplicaciones pueden seguir enumerando monitores.

El nombre visible del filtro personal es **Microfono solo mi voz**. Si ya estaba activo con el nombre anterior, reinicia únicamente `dotfiles-microphone.service` para recrear esa entrada. Esto interrumpe las capturas personales abiertas durante el reinicio.

## Activar reconocimiento sobre audio original

Las pruebas comparativas locales favorecieron reconocer desde audio original. Los perfiles nuevos, tanto desde el panel como por CLI, usan esa ruta:

```bash
dotfiles-microphone configure-profile "Carlos original"
```

Lee el párrafo durante los 15 segundos que indica el contador. El registro usa PCM float32 original a 16 kHz y guarda un factor de margen para evitar recorte por conversión. No reemplaza los perfiles anteriores ni intenta convertir una huella creada después de RNNoise. El panel distingue `audio original` de `perfil anterior, audio filtrado`. Tras actualizar desde el programa anterior, apaga y enciende Solo mi voz una vez para cargar el supervisor nuevo; no hace falta reiniciar el servicio de ruido. Después elige **Microfono solo mi voz** en la aplicación de prueba.

Con un perfil original, el trabajador captura el micrófono físico una sola vez en float32 a 48 kHz. Cada frame de 10 ms se bifurca hacia reconocimiento original y RNNoise nativo; un FIR continuo de 63 taps convierte únicamente el reconocimiento a 16 kHz. La salida limpiada conserva los 48 kHz nativos de RNNoise, incluidos los componentes por encima de 8 kHz, sin reducirla a 16 kHz y volver a ampliarla. La misma decisión de identidad se aplica a los 160 ms correspondientes de salida, manteniendo los umbrales y el perfil. La rama original se retrasa por el retardo medido del denoiser para emparejarla con la salida limpiada antes de aplicar la decisión del mismo bloque. La medición usa señal sintética en RAM y reinicia RNNoise antes de escuchar el micrófono; en la biblioteca local se observaron 20 ms. Se rechaza una biblioteca incompatible en lugar de emitir audio desincronizado.

El adaptador usa los símbolos C de RNNoise de `librnnoise_ladspa.so`, ya instalado por el componente, y lee el volumen actual de la fuente de ruido mediante libpulse. En la salida nativa de 48 kHz, el factor de margen del perfil se aplica únicamente al reconocimiento; RNNoise recibe la señal física flotante, sin recortar sus picos a ±1 antes de procesarlos. La salida conserva el volumen de la fuente normal. La ruta anterior de 16 kHz conserva su escalado histórico. No mezcla capturas de dos fuentes ni añade la recuperación retrospectiva de 100 ms del filtro normal a esta ruta. El filtrado nativo de salida es propio del trabajador personal y se libera con él. El servicio RNNoise normal conserva su configuración.

El estado activo publica `recognition_route`, `source`, `noise_output`, `noise_delay_ms` y `pipeline_version: 7`. El estado también incluye `audio_levels`: picos acumulados de entrada y salida y número de muestras fuera de rango antes de convertir a PCM16, para comprobar saturación sin guardar audio. La salida usa un único reloj de 10 ms para silencio y voz: rellenar un hueco no permite luego emitir una ráfaga adicional que acumule audio dentro del pipe. Cada publicación de estado incluye `window_blocks`, `window_passing_blocks`, `window_probability_min` y `window_probability_max` para detectar aperturas breves entre las instantáneas. Al cambiar de perfil se descarta el trabajador anterior y se inicia uno nuevo, con captura, estados de filtro y ganancia correspondientes; ese cambio no consume los reintentos por fallo. La ruta original debe validarse hablando tú y hablando otra persona mientras permaneces callado. La mejora observada en el comparador no garantiza rechazo total ni separación de voces simultáneas.

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
python3 -m unittest discover -s tests/voice-isolation
```

El servicio y sus comandos se ejecutan en el host. Apagar Solo mi voz guarda `personal: false` y detiene el proceso sin eliminar el enlace de su unidad de systemd. Si el enlace falta por una desactivación anterior, el panel lo restaura desde el componente instalado al encender el filtro.

Solo mi voz solicita búferes de captura y reproducción de 20 ms, sin buffering de los archivos de Python. Captura, inferencia y reproducción trabajan por separado. La captura lee frames de 10 ms: PCM16 a 16 kHz en la ruta anterior o float32 a 48 kHz en la original. El modelo recibe 16 kHz y reúne 16 frames (160 ms); su decisión se aplica al bloque de salida emparejado. La salida de perfiles originales usa PCM16 a 48 kHz; la ruta anterior conserva 16 kHz. El estado publica `output_rate`. Ambas entregan frames de 10 ms. La ruta original aplica una rampa de apertura de coseno elevado de 10 ms; los perfiles anteriores conservan 5 ms. La rampa solo atenúa audio ya aceptado y no abre ante una voz rechazada ni añade una espera de reproducción. Las colas de captura y salida admiten 32 frames cada una (320 ms de capacidad, no un retraso fijo). La salida entrega ceros cuando no tiene resultados disponibles.

La secuencia y el reloj monotónico permiten detectar resultados atrasados. La prueba se detiene al saturar una cola o superar 480 ms desde el comienzo estimado del bloque; no continúa reproduciendo voz atrasada ni cambia a audio sin filtrar. Este tiempo se estima desde la primera lectura del proceso y no incluye todos los búferes del servidor o de la aplicación. El estado añade `capture_queue_ms`, `playback_queue_ms`, `block_age_ms`, `sequence` y la versión del flujo. Los errores detienen únicamente el procesamiento personal; RNNoise normal permanece disponible.

El modelo usa hasta ocho hilos de CPU para reducir el tiempo de inferencia, limitado por los procesadores disponibles. Esto no cambia el perfil ni los umbrales. En la comprobación local con el mismo audio, la mediana pasó de unos 108 ms con cuatro hilos a 93 ms con ocho, con diferencias de puntuación inferiores a 0,000001. No es una medición del retraso completo hasta la aplicación; los bloques de 160 ms y los búferes de audio siguen sumando tiempo.

En perfiles originales, tres bloques consecutivos con RMS de reconocimiento ≤0,002 y puntuación <0,45 limpian la ventana de análisis. Esto elimina el contexto de silencio, conservando el embedding inscrito y exigiendo nuevamente ≥0,60 para abrir; no se acepta una voz por haber reconocido la frase anterior. El audio muy bajo sigue analizándose. El estado publica `input_rms`, `recognition_in_pause`, `recognition_context_resets` y `gate_attack_ms`. Esta condición conservadora puede no activarse en un ambiente ruidoso; no garantiza recuperar todas las sílabas.

El supervisor del host escucha los eventos de PulseAudio/PipeWire y no importa PyTorch ni carga el modelo en reposo. Las capturas de Aislamiento de voz o del micrófono físico no activan el reconocimiento personal. Cambiar de perfil conserva los ajustes de latencia y de detección.

## Prueba guiada de la salida actual

Para repetir la prueba del perfil seleccionado sin crear ni modificar perfiles:

```bash
python3 libexec/dotfiles-voice-probe
```

Ejecuta el comando desde la raíz del repositorio. La pantalla espera Enter antes de conectar el micrófono y antes de la prueba, con cinco segundos de preparación en silencio. Por defecto prueba únicamente tu voz: lee cuatro segundos, calla dos y vuelve a leer cuatro. El contador indica cuándo callar y retomar el párrafo; el informe marca `expected_action` para distinguir la pausa prevista de un corte. Para probar por separado el rechazo de otra persona, usa `--otras-voces`: esa persona lee diez segundos mientras tú permaneces callado y el resultado se guarda en `/tmp/otras-voces-prueba.jsonl`. Comprueba el perfil, la ruta y la versión del procesamiento activo antes de comenzar. Mide la salida hacia las aplicaciones y guarda únicamente métricas y estados en `/tmp/solo-mi-voz-prueba.jsonl`; el audio se descarta. Terminar o cancelar cierra la captura de prueba. `--preview` permite ver el diseño sin abrir el micrófono.

## Comparar reconocimiento original y filtrado

La técnica de `mac_os` de reconocer sobre audio original puede evaluarse sin modificar los perfiles actuales ni el servicio de ruido. Cierra otras capturas de Solo mi voz y ejecuta:

```bash
dotfiles-microphone compare-voice
```

La prueba carga el modelo, prepara cada etapa con una cuenta atrás y captura ambas rutas durante las mismas intervenciones: 15 segundos de registro solo tuyo, 12 segundos de prueba tuya y 12 segundos de otra persona mientras tú permaneces callado. El micrófono físico, puerto, ganancias y dispositivo predeterminado no cambian. El audio y los perfiles temporales permanecen en RAM y se descartan al salir; los perfiles guardados no se reemplazan ni se selecciona uno diferente.

Cada etapa muestra un párrafo continuo para leer a ritmo natural hasta terminar el contador; no hace falta acabar el texto. Debajo avanzan los segundos y el nivel RMS de ambas rutas. El medidor indica audio recibido; no transcribe ni acredita que sea la persona del perfil. Al terminar el registro valida ambas rutas antes de pedir las otras dos etapas. Si una falla, informa la ruta y el nivel o posible saturación, guarda estas métricas en `enrollment_levels` y termina con un mensaje legible.

El comparador captura PCM float32 de 16 kHz para conservar valores que excedan el rango de PCM16 sin recortarlos durante esa conversión. Calcula un factor de margen por ruta con el registro y aplica ese mismo factor en RAM al registro y a ambas pruebas; no altera volumen, ganancia física ni los perfiles guardados. Conserva el pico, RMS y fracción fuera de rango originales en el informe, junto con el factor aplicado. Valores altos flotantes se muestran como `ALTA`; muchos picos iguales se señalan como posible recorte previo y se rechaza ese registro mediante una heurística, pues reducir el nivel no recupera una forma de onda ya recortada. Esto prepara una medición, no corrige por sí solo errores de identidad.

Tras capturar, procesa las dos rutas sin la restricción de tiempo real para no acumular retraso al ejecutar dos inferencias. Usa un registro temporal original para puntuar audio original y uno filtrado para puntuar audio filtrado. Excluye los extremos de captura y separa los primeros 2,4 segundos de contexto del modelo de las métricas de régimen estable. Informa la fracción de bloques que el filtro deja pasar en cada etapa, las puntuaciones y los tiempos de inferencia. La fase está indicada por el usuario; las fracciones no son probabilidades calibradas de identidad ni una medición del retraso completo.

El resultado queda en `~/.config/voice-isolation/voice-comparison.json`, sin audio ni embeddings. Compara tanto el rechazo ajeno como la conservación de tu voz. Los perfiles originales nuevos usan la ruta seleccionada a partir de esa comparación; los anteriores conservan su ruta y sirven de referencia. No se promete aislamiento por integrar estas colas o por ejecutar un modelo.
