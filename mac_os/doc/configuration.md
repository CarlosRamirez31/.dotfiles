# Configuración por entorno

El host carga Options una sola vez antes de iniciar logs y servicio. Los módulos reciben sus opciones
por inyección; el hijo recibe el snapshot validado por el canal de arranque. No se modifica el entorno
global ni se vuelven a leer archivos desde módulos o callbacks de audio.

Desde `mac_os/`:

```bash
cp .env.example .env
MIC_ENV_FILE="$PWD/.env" pnpm run tauri dev
# Una variable del proceso tiene precedencia sobre el archivo:
MIC_ENV_FILE="$PWD/.env" MIC_VOICE_THRESHOLD=0.8 pnpm run tauri dev
```

Sin `MIC_ENV_FILE` se utilizan defaults y variables del proceso. La app instalada no busca `.env` en
su directorio de trabajo: para usar un archivo se inicia el ejecutable con esa variable explícita.
El archivo admite `CLAVE=valor`, comillas simples/dobles envolventes, líneas vacías y comentarios en
líneas separadas. No admite expansión de variables, ejecución shell, `export`, comentarios inline ni
claves repetidas. Se rechazan claves desconocidas y valores inválidos, sin registrar sus valores.

| Variable                  | Default                              | Rango / significado                                            |
| ------------------------- | ------------------------------------ | -------------------------------------------------------------- |
| `MIC_LOG_RETENTION_DAYS`  | 30                                   | 1–365 días completos por partición UTC                         |
| `MIC_LOG_CLEANUP_SECONDS` | 3600                                 | 60–86400; limpieza también al arrancar                         |
| `MIC_MAX_PENDING`         | 16                                   | 1–128 operaciones activas                                      |
| `MIC_MAX_OPERATIONS`      | 10000                                | 100–100000; capacidad del historial                            |
| `MIC_EVENT_BATCH`         | 64                                   | 1–1024 eventos por lote SSE                                    |
| `MIC_MODEL_LOAD_SECONDS`  | 120                                  | 1–600; plazo de carga personal                                 |
| `MIC_INFERENCE_SECONDS`   | 2                                    | 1–30; plazo de respuesta personal                              |
| `MIC_ENROLL_SECONDS`      | 60                                   | 1–300; plazo de cálculo del registro, no duración de grabación |
| `MIC_VOICE_THRESHOLD`     | 0.7                                  | Número finito entre 0 y 1                                      |
| `MIC_VOICE_RUNTIME`       | Ruta de desarrollo o datos de la app | Ruta absoluta al runtime privado                               |
| `MIC_STARTUP_SECONDS`     | 30                                   | 1–300; handshake del servicio                                  |
| `MIC_SSE_RECONNECT_MS`    | 1500                                 | 100–30000; espera entre reconexiones del cliente               |

React recibe solo la espera de reconexión mediante `public_options`; la conexión efímera sigue usando
`local_connection`. No se exponen todas las opciones, rutas privadas ni claves. La URL loopback, el token
aleatorio, los hashes de modelos, formatos PCM compatibles y cifrado obligatorio son invariantes. No hay
URL Cloud configurable porque todavía no hay adaptador remoto. La versión firmada del producto permanece
como configuración de build en manifiestos, no como un override de ejecución.

Los logs están en `local-service/logs/` dentro de los datos de la app: `host.FECHA.jsonl`,
`service.FECHA.jsonl` y `business.FECHA.jsonl`. Se conservan archivos activos y se eliminan únicamente
particiones propias vencidas, sin seguir enlaces simbólicos. La copia de eventos contiene ID, tipo, módulo,
fecha, versión y estado; excluye comandos, detalles libres y datos de voz. No elimina eventos de SQLCipher.

## Cierre del servicio

`MIC_SHUTDOWN_SECONDS` (5 por defecto; rango 1–30) establece el plazo de cierre cooperativo.
El host cierra stdin y espera; si el hijo no termina, lo finaliza y recoge su estado. El servicio aplica también
un plazo al drenaje para no depender del host cuando este muere. En un cierre forzado, los trabajos pendientes
se recuperan desde SQLCipher en el siguiente arranque; nunca se reanuda captura automáticamente.
El timeout no es una confirmación de persistencia ni de liberación cooperativa: queda registrado como fallo.

`MIC_MAX_VOICE_PROFILES` configura el máximo de voces guardadas (32 por defecto; rango 1–128). Las voces existentes no se eliminan al reducir el límite; se rechazan nuevas altas hasta quedar por debajo del límite.

La versión del prefijo HTTP se configura con `MIC_API_VERSION` (por defecto `v1`).
Options valida el formato y el handshake informa `apiVersion` al cliente, que usa el mismo prefijo.
