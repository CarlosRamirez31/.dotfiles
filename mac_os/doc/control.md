# Control HTTP/SSE implementado

Decisión confirmada: el BFF también vive en el servicio Local. Sustituye la propuesta anterior de control
IPC/gRPC. Tauri solo supervisa y entrega dirección/credencial por IPC; React usa HTTP/SSE.

## Contrato v1

| Solicitud                           | Efecto                                                                        |
| ----------------------------------- | ----------------------------------------------------------------------------- |
| `GET /v1/audio/devices`             | Consulta síncrona de entradas y presencia de BlackHole 2ch; no captura.       |
| `GET /v1/operations`                | Últimas 100 operaciones, incluida una sesión de audio activa.                 |
| `GET /v1/operations/{id}`           | Estado persistido por identificador, también después de reiniciar.            |
| `POST /v1/operations/storage-check` | Diagnóstico real de integridad; sin cuerpo.                                   |
| `POST /v1/commands`                 | Comando tipado `check_storage`, `start_audio` o `enroll_voice`.               |
| `POST /v1/operations/{id}/cancel`   | Cancela un pendiente o solicita detener el trabajo en curso.                  |
| `GET /v1/events`                    | SSE con `id`, nombre del evento y JSON correlacionado mediante `operationId`. |

Los POST de trabajo exigen `Idempotency-Key` alfanumérica/con guion de 1–128 caracteres. La clave y el comando
completo se guardan; repetirlos devuelve la misma operación, y reutilizar la clave con otros parámetros da
`409`. Se confirma transaccionalmente operación + evento antes del `202 Accepted`, que incluye `Location`.
El worker ejecuta después y fuera del ciclo HTTP. Un `202` no significa procesamiento completado.

`start_audio` recibe `input_id` y `personal_voice`; `enroll_voice` recibe `input_id`. El contrato rechaza
campos desconocidos. Un único comando de audio/registro puede estar pendiente o activo. No existe todavía
un contrato público para cambiar ajustes o múltiples perfiles; cuando se añada, guardar ajustes simples
será una operación inmediata, sin job innecesario.

## Ejecución y eventos

Un inbox SQLCipher almacena los comandos. Tokio Notify despierta al único trabajador; no transporta PCM ni
es la fuente de verdad. No había infraestructura de mensajería previa que reutilizar. No se añade broker,
contenedor, bus genérico, saga ni un proceso por módulo.

Estados: `accepted → running → succeeded|failed|cancelled|interrupted`; cancelar en ejecución pasa por
`cancellation_requested`. Los eventos `operation.accepted`, `started`, `progress`, `succeeded`, `failed`,
`cancellation_requested`, `cancelled` e `interrupted` expresan hechos ya persistidos. Incluyen versión,
módulo, secuencia global local, fecha UTC, operationId y snapshot. No incluyen PCM ni embeddings.

Una sesión de audio permanece `running` hasta detenerla; `detail=audio_active` distingue captura real de
carga de modelo. El registro informa cuándo hablar y cuándo calcula el perfil. El filtro de voz falla
explícitamente si faltan runtime, pesos o registro; no cae al modo de ruido silenciosamente.

## Persistencia y recuperación

Reinicio: los trabajos iniciados quedan interrumpidos; una cancelación solicitada queda cancelada.
**Nunca** se reanuda captura ni registro, ni siquiera si habían quedado en cola. Solo los diagnósticos
pendientes pueden continuar. No hay reintentos automáticos de inferencia o de apertura de micrófono.
El cliente reintenta peticiones ambiguas con la misma clave y reconecta SSE con `Last-Event-ID`.

SSE lee lotes de hasta 64 eventos desde SQLCipher; un lector lento no detiene el trabajador. Los IDs no se
reinician mientras se conserva la DB. Cursor inválido/futuro: `400`; el cliente conserva historial visible
si pierde conexión. No se purga el historial en esta entrega: límite explícito de 10.000 operaciones y
16 no terminadas; exceso devuelve `503`. Antes de beta se necesita política de retención/limpieza y
paginación de historial. No se promete entrega exactamente una vez: consumidores usan los IDs.

## Acceso y ciclo de vida

Escucha exclusivamente `127.0.0.1` en puerto asignado por el sistema. Token aleatorio por lanzamiento,
`Authorization: Bearer`, nunca en URL, localStorage o logs. Origen Tauri permitido; localhost:1420 solo en
debug. No hay login: el acceso se concede al frontend de la instancia. CORS no sustituye el token.

Bloqueo de archivo por directorio de datos, handshake de versión, plazo de arranque y detección de EOF del
padre. El cierre detiene el hijo; el worker Python comprueba además que su padre siga vivo. Keychain denegado
o DB ilegible impiden arrancar sin reemplazar datos. Falta una pantalla de recuperación/reintento para ese
error de arranque; hoy se devuelve error de inicio de Tauri. No hay reinicio automático del servicio.

Fuentes: [Axum SSE](https://docs.rs/axum/0.8.9/axum/response/sse/),
[Tokio Notify](https://docs.rs/tokio/latest/tokio/sync/struct.Notify.html),
[SQLCipher](https://www.zetetic.net/sqlcipher/).
