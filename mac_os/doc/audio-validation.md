# T003 — Audio real: evidencia de desarrollo

Pruebas realizadas el 20 de octubre de 2026 en macOS 27.0.1, Apple Silicon.
BlackHole 2ch 0.7.1 instalado mediante el instalador oficial autorizado por el usuario.
CoreAudio enumeró entrada/salida virtual estéreo a 48 kHz y micrófono integrado mono a 48 kHz.
Los dispositivos predeterminados del sistema permanecieron en micrófono y altavoces integrados.

## Recorrido observado

- Micrófono físico → RNNoise → BlackHole → FFmpeg, con PCM float32 estéreo a 48 kHz.
- Señal controlada: frase sintética reproducida por altavoces. La medición se mantuvo en RAM;
  no se guardaron grabaciones privadas ni muestras en Git.
- Antes de activar: 2 915 328 muestras float, pico y RMS cero.
- Durante la sesión: 2 940 928 muestras, pico 0.277888 y RMS máximo por ventana 0.045497.
- Tras cancelar, mientras se reproducía otra frase: 643 072 muestras, todas cero.
- El sondeo CoreAudio confirmó dispositivos liberados después de cancelar.

Estas cifras prueban señal recibida y silencio tras parar. No prueban latencia, calidad de reducción,
continuidad sin pérdida de bloques ni compatibilidad con aplicaciones de llamadas.

## Salida durante inferencia personal

Con captura e inferencia activas se observaban host, servicio y worker Python.
Al salir con ⌘Q desaparecieron los tres procesos y CoreAudio indicó micrófono y BlackHole inactivos.
El log registró desconexión a las 23:12:19.717 UTC y servicio detenido a las 23:12:19.772 UTC
(unos 55 ms en esa ejecución; no es un SLA). La operación quedó cancelada.

La migración del perfil anterior también se observó en la UI como «Voz anterior · Predeterminada».
Los cambios posteriores de hooks/controladores tienen pruebas automatizadas; todavía falta repetir
el recorrido visual completo sobre el bundle final de esta entrega.

## Reproducción y pendientes

`pnpm test audio-hardware --seconds 6 --expect silence` verifica reposo sin guardar audio.
Con sesión activa, `pnpm test audio-hardware --seconds 12 --speak --expect signal` mide señal controlada.
El comando requiere FFmpeg y BlackHole de desarrollo; no forma parte de CI automático.

Pendientes: salir durante registro de voz, caída del servicio con captura activa y recuperación visible;
formato no soportado, pérdida de entrada y error de salida. T002/T003 siguen abiertos.
T004 debe distinguir productor de consumidores; el indicador agregado de CoreAudio no demuestra eso.
