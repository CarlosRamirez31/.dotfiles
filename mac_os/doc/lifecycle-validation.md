# T002 — Supervisión y cierre: evidencia

Fecha: 20 de octubre de 2026. macOS Apple Silicon; código local posterior a `a39537e`.
Estado: implementación y pruebas de procesos completadas; aceptación con captura activa pendiente de T003.
La primera fase de esta evidencia se ejecutó sin captura ni driver. Posteriormente se instaló BlackHole
y se comprobó salida durante captura/inferencia: ver [audio real](audio-validation.md).

## Cambios

- Salida explícita de Tauri llama al supervisor: cierre de stdin, espera cooperativa y finalización forzada
  solo al vencer `MIC_SHUTDOWN_SECONDS`. Drop reutiliza el cierre y las llamadas repetidas son seguras.
- El servicio espera al worker antes de salir y mantiene el lock hasta terminar. Tiene su propio plazo de
  drenaje para el caso de muerte del host; no espera indefinidamente a tareas bloqueadas del runtime.
- La parada es persistente: despierta al worker ocioso, impide ejecutar nuevos handlers y no pierde la
  cancelación entre reclamar un trabajo y registrar su ejecución. Confirma resultado/cancelación en SQLCipher.
- El worker Python recibe el PID esperado del padre y activa vigilancia antes de importar/cargar la IA.
  Rechaza un arranque ya huérfano. El smoke test usa el mismo contrato privado; HTTP/SSE no cambian.
- No se cambió el comportamiento de la ventana actual: ocultar conserva la app; cerrar la última ventana
  sale. El futuro popover tendrá su comportamiento propio en T006.

## Verificaciones

| Caso                             | Evidencia / límite                                                                                 |
| -------------------------------- | -------------------------------------------------------------------------------------------------- |
| Handshake ausente                | Binario real en modo servicio sale con error al recibir EOF sin lanzamiento                        |
| Instancia duplicada              | Segundo servicio rechazado con el mismo directorio; original sigue atendiendo                      |
| Cierre cooperativo               | Servicio real sale con código 0 tras EOF; prueba inicial ~4 ms                                     |
| Reinicio                         | Lock liberado; abre de nuevo la base temporal cifrada                                              |
| Supervisor terminado con SIGKILL | Servicio real deja de existir; prueba inicial ~8 ms                                                |
| Worker IA y muerte de su padre   | Worker real cargado deja de existir; prueba inicial ~322 ms                                        |
| Worker durante arranque          | Suite incluye muerte del padre antes de esperar readiness                                          |
| Handler activo / worker ocioso   | Tests Rust verifican espera, cancelación persistida, despertar y no ejecutar cola tras parada      |
| Proceso que no coopera           | Test con proceso auxiliar verifica plazo de cierre y recolección del hijo; no simula IA            |
| Ocultar ventana                  | Bundle debug actualizado: host 46239 y servicio 46258 permanecieron vivos tras ⌘H                  |
| Salir con ⌘Q                     | Esos dos PID desaparecieron; `service.parent_disconnected` y `service.stopped` a las 22:56:22 UTC  |
| Cerrar última ventana            | Segundo arranque: host 46552 y servicio 46568 desaparecieron; cierre registrado a las 22:56:52 UTC |

Prueba adicional del host Tauri real: SIGKILL al PID 64543, servicio 64552 terminado en 81 ms; se verificaron ruta y relación padre/hijo antes de enviar la señal. Sin captura activa.

Los tiempos son observaciones de una ejecución local, no un SLA. Los PID identifican únicamente esta sesión.
La prueba inicial con ejecutable suelto falló por timeout de arranque. macOS abrió además un bundle release
anterior al resolver el nombre de la app: se descartó esa ejecución como evidencia del cambio. Se construyó
un bundle debug nuevo y se verificó su ruta/PID antes de las pruebas visuales de la tabla.

## Reproducción

Desde `mac_os/`:

```bash
pnpm test
pnpm test lifecycle
pnpm test models
cargo clippy --locked --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings
pnpm tauri build --debug --bundles app
```

`lifecycle` usa procesos reales, loopback, Keychain y bases temporales. Requiere runtime/modelos privados
instalados; no descarga modelos. El harness actúa como supervisor de prueba; las acciones ⌘H/⌘Q/cerrar se
probaron por separado con la app Tauri real. No se atribuye a los tests de procesos cobertura visual.

## Pendiente para cerrar T002 completamente

T003 debe comprobar una captura real, salir durante captura/registro/inferencia y medir que el dispositivo y
los workers se liberan. También falta verificar en ese recorrido la caída del servicio durante captura y la
recuperación visible. La ausencia de procesos en reposo no demuestra liberación de un micrófono activo.
No marcar F02/F12 ni S01 completos por estos resultados; F12 requiere además detección real de consumidores.

## Resultado automatizado de esta entrega

- 24 pruebas Rust normales aprobadas; prueba adicional del adaptador con modelo real aprobada por separado.
- 5 pruebas Node y 4 Python aprobadas.
- Suite `lifecycle` aprobada: handshake, duplicado, EOF, reinicio, caída del supervisor del servicio,
  caída del padre del worker cargado y durante su arranque.
- TypeScript y build React aprobados al construir el bundle debug de 45.79 MiB; no es instalador firmado.
- Clippy con `-D warnings`, Prettier, rustfmt, Ruff y ESLint del runner aprobados. No se modificaron dependencias.

## Actualización tras T003

La salida durante captura e inferencia personal liberó host, servicio, worker y dispositivos.
Quedan el cierre durante registro y la caída del servicio con captura activa/recuperación visible.
Los resultados automatizados anteriores son históricos; la revisión posterior tiene 30 pruebas Rust
y 10 frontend aprobadas, con el ensayo de modelo privado omitido en la suite normal.
