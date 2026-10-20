# Convenciones de arquitectura aprobadas

Estas decisiones complementan [architecture.md](architecture.md). Son requisitos de implementación; el
apartado final distingue las adaptaciones pendientes. Se aplican a React, Rust y al runtime Python.

## Options y configuración por entorno

La configuración entra por el composition root (`bootstrap`), se convierte en opciones tipadas, se valida
antes de arrancar servicios y se inyecta por constructor o factoría. Los módulos no leen `.env`,
`process.env` ni variables del sistema directamente. Dominio y casos de uso reciben únicamente las
opciones que necesitan, sin depender del mecanismo de carga.

Precedencia: valores seguros por defecto → archivo `.env` seleccionado explícitamente → variables del
proceso. `.env.example` documentará nombres, unidades, valores de ejemplo y restricciones sin secretos.
No se buscarán archivos de configuración arbitrarios en el directorio de trabajo de una app instalada.
Una opción inválida impedirá arrancar la capacidad afectada con un error comprensible; no se ignorará.
El primer alcance usa una instantánea inmutable al arrancar, sin recarga dinámica.

Cada módulo será dueño de sus opciones: `AudioOptions`, `PersonalVoiceOptions`, `OperationsOptions`.
Commons contendrá mecanismos compartidos y opciones técnicas, como `LoggingOptions`; no un objeto global
con toda la configuración de negocio. Rust empleará structs, TypeScript interfaces readonly y Python
objetos tipados inmutables. Bootstrap construirá los adaptadores e inyectará sus opciones.

Serán configurables, con rangos validados, los timeouts, tamaños de colas, rutas de modelos, umbrales de
voz, retención de diagnóstico y URLs de adaptadores remotos. No se permitirá alterar mediante entorno
invariantes como autorización local, cifrado obligatorio, verificación de modelos o límites de formatos
admitidos. Una URL remota no autoriza enviar audio: requiere la edición, consentimiento y contrato adecuados.

La conexión Local conserva dirección loopback y puerto asignado por el servicio; no se fija una URL de
producción en React. La UI recibe la conexión mediante el host. Las opciones públicas se exponen con una
lista permitida; nunca se serializa el entorno completo ni se ponen secretos en variables `VITE_*`.
Claves de SQLCipher y credenciales persistentes permanecen en Keychain, no en `.env` ni en logs.

La versión de producto es configuración de **compilación**, sincronizada entre los manifiestos de frontend,
Rust y Tauri por el proceso de release. Cambiar `.env` en una instalación no cambiará su versión firmada.
Versiones de dependencias permanecen fijadas en manifiestos/lockfiles; modelos en manifiestos con hashes.
Los ajustes personales editables pertenecen a perfiles persistidos, no a variables de despliegue.

## Puertos, adaptadores, Result y ACL

Cada capacidad define su puerto con tipos propios en aplicación/dominio. La infraestructura implementa
el adaptador del proveedor. Su capa anticorrupción (ACL) valida y traduce respuestas, unidades, formatos,
estados y errores al lenguaje de la capacidad. No se filtran SDK, tensores, excepciones, DTO ni códigos
HTTP del proveedor al negocio o al BFF. La ACL puede ser una función o archivo dentro del adaptador;
no requiere otro servicio, bus ni jerarquía de clases.

Las operaciones fallibles de IA local y remota retornan un Result tipado: éxito con valor o fallo con un
error conocido. Rust usa `Result<T, CapabilityError>`; TypeScript una unión discriminada `ok/value/error`;
Python una unión tipada de éxito/fallo. No se usará una envoltura adicional para resultados Rust ni se
convertirá un fallo de inferencia en éxito con audio vacío o probabilidad cero.

Los errores propios distinguirán entrada inválida, modelo no disponible, timeout, cancelación, saturación,
respuesta incompatible y fallo de inferencia. El adaptador captura excepciones esperables en su frontera
y las traduce; errores de programación no se ocultan como errores de negocio recuperables. Mensajes
externos y datos sensibles no se devuelven al cliente. La aplicación decide reintentos acotados según
idempotencia y plazo; el adaptador no reintenta indiscriminadamente sesiones ni bloques de audio.

El BFF traduce el resultado propio a HTTP o al resultado de la operación, sin conocer al proveedor.
Los eventos comunican transiciones confirmadas; Result comunica el resultado directo de una llamada.
No son mecanismos intercambiables. Python mantiene los adaptadores en `runtime/adapters/<modulo>/` y
puertos sin dependencias de SDK. Las capas Rust/React son carpetas con archivos por responsabilidad.

## Event-driven para hechos de negocio

Se conserva el monolito modular y su mensajería interna, sin broker externo. Un comando solicita una
acción; un evento expresa un hecho ocurrido: operación aceptada, sesión iniciada, perfil registrado,
operación completada o fallida. Los módulos publican hechos mediante contratos internos versionados,
correlacionados por `operationId`; no llaman a la infraestructura privada de otro módulo.

Consultas y configuraciones inmediatas no se convierten artificialmente en trabajos. Para trabajo
asíncrono, el BFF persiste la aceptación, devuelve `202` y el worker procesa fuera de la petición. SSE
notifica transiciones persistidas. Se reutilizan journal e inbox existentes; no se incorpora un bus
universal ni sagas hasta que un flujo real lo justifique.

El bus de negocio no transporta bloques PCM, muestras, tensores, mensajes de debug ni estadísticas por
frame. El audio usa canales acotados. Logs técnicos usan el sistema de logging, y SSE es un transporte de
notificaciones del cliente, no el bus interno. Los consumidores deben tolerar reentrega; no se promete
entrega exactamente una vez. Véase [control.md](control.md).

## Logs locales y eventos persistidos

Decisión confirmada: `logs/` guarda logs técnicos de cliente/host y servicio, más una **copia diagnóstica**
de eventos de negocio. SQLCipher sigue siendo la fuente de recuperación de estado y replay SSE. Borrar
archivos de diagnóstico no borra operaciones ni eventos de recuperación de la base.

Los archivos se organizan por origen y fecha, en formato estructurado, con fecha UTC, severidad, código,
módulo y correlación cuando corresponda. No incluyen audio, embeddings, tokens, claves, cabeceras,
cuerpos de peticiones ni datos arbitrarios de proveedores. La copia de eventos utiliza campos permitidos,
no el documento completo de operación que pueda contener comandos o información personal.

La retención predeterminada es **30 días de antigüedad**, configurable mediante `LoggingOptions` con
validación. Se limpiarán archivos vencidos al iniciar y periódicamente mientras la app esté abierta;
no habrá un servicio permanente de limpieza. La limpieza se limita a archivos reconocidos de la carpeta
propia, evita seguir enlaces simbólicos y no elimina archivos abiertos ni rutas arbitrarias. Limitar el
número de archivos no equivale a retención por días. Los errores de escritura/limpieza no detienen audio;
se informan de forma acotada sin recursión de logging. No se escribe disco desde el callback de audio.

La copia de diagnóstico no condiciona el commit del evento de negocio ni sustituye un registro de auditoría.
La política de poda del journal SQLCipher se define separadamente: no se deduce de estos 30 días, y debe
preservar la recuperación SSE o proporcionar una resincronización explícita.

Cloud tendrá OpenTelemetry para trazas, métricas y logs, con exportación configurable y desactivada si no
hay destino. La correlación de trabajos asíncronos mantendrá `operationId` y contexto de traza; IDs de
operaciones no serán etiquetas de métricas. El cliente no recibirá credenciales administrativas del
exportador. Esta integración Cloud es diseño pendiente, no implementación Local.

## Seguridad SQL y consultas por lotes

Todos los valores se enlazan mediante parámetros; no se concatenan entradas de UI, entorno, comandos o
proveedores en SQL. Los identificadores SQL dinámicos, si fueran necesarios, se eligen exclusivamente de
una lista interna permitida; los parámetros no sustituyen nombres de tablas/columnas. Las migraciones
usan sentencias controladas por el proyecto.

Listados, recuperación y relaciones usan consultas por lotes, joins o lecturas agrupadas y paginadas.
No se consulta una relación por cada fila ni se ejecuta una cadena de actualizaciones individuales cuando
una operación de conjunto puede expresar el mismo contrato. Las pruebas verifican tanto entradas con
contenido SQL tratadas como datos como el número acotado de consultas al crecer el lote. No se cambia la
semántica transaccional para reducir consultas.

## Pruebas por módulo y entrada central

`mac_os/test/` es la entrada central de ejecución y de pruebas entre módulos. Cada módulo guarda sus
pruebas en su propia carpeta `test/`, cerca de la implementación. La entrada central las registra o ejecuta
con el runner nativo de cada lenguaje; no duplica casos ni importa código de pruebas en producción.

```text
mac_os/
  test/                                 # orquestación y pruebas entre módulos
    integration/
  src/modules/<modulo>/test/             # React/TypeScript
  src/commons/test/                      # utilidades compartidas
  src-tauri/src/modules/<modulo>/test/    # Rust, registro con cfg(test)
  src-tauri/src/commons/test/
  runtime/adapters/<modulo>/test/         # Python, contrato y adaptador real
```

No se crean suites vacías para módulos futuros. Rust registra sus suites exclusivamente bajo `cfg(test)`;
el runner central invoca Cargo. Node ejecuta las suites frontend registradas; Python usa su runner propio.
El comando central deberá fallar si falla cualquier suite requerida y distinguir unitarias, integración,
modelos y hardware. Pruebas que requieren pesos, driver o micrófono se ejecutan explícitamente, nunca se
presentan como aprobadas al omitirse. Fixtures deben ser pequeñas, licenciadas o consentidas; pesos,
grabaciones privadas y secretos quedan fuera de Git.

Cada módulo prueba invariantes y contratos, traducciones ACL, éxito/error Result, opciones inválidas y
cancelación según su responsabilidad. Integración central verifica HTTP/SSE, recuperación SQLCipher,
ciclo de vida y comunicación entre capacidades. Los detalles de aceptación están en [testing.md](testing.md).

## Estado de adopción

Implementado: Options tipadas cargadas en bootstrap, precedencia de entorno, validación y snapshot enviado
al servicio; Result y ACL en RNNoise, nomo-pvad/Python y adaptadores HTTP React; pruebas en carpetas `test/`
de los módulos con runner central; retención temporal de logs y copia de metadatos de eventos confirmados.

Las opciones admitidas y comandos están en [configuration.md](configuration.md). `pnpm test` ejecuta Node,
Cargo y las pruebas Python sin modelos. `pnpm run test:models` ejecuta explícitamente el adaptador real
con el runtime instalado. Los tests Rust se registran desde `test/rust.rs` únicamente bajo `cfg(test)`.

Los archivos diarios se eliminan cuando su partición completa supera 30 días; esto puede conservar las
primeras entradas de una partición hasta un día adicional. Cada proceso limpia sus archivos y protege
los que mantiene abiertos, incluso después de un período prolongado sin escribir. El hilo de mantenimiento
termina al cerrar la app. SQLCipher no se poda mediante esta limpieza.

La copia diagnóstica usa una cola acotada y puede perder entradas por saturación o cierre abrupto; no se
reconstruye retroactivamente. El journal cifrado sigue siendo la fuente durable de recuperación. Las
integraciones Cloud y OpenTelemetry siguen pendientes: no se simulan proveedores remotos ni su validación.

### Inyección de voz personal

`LocalHandler` recibe `EnrollmentFactory` y `PersonalVoiceFactory` por inyección. La primera prepara una
`EnrollmentSession` antes de capturar audio; la segunda entrega el puerto `PersonalVoice` para el filtro.
Bootstrap elige `NomoFactory`, que concentra rutas del runtime y `VoiceOptions`. Solo la infraestructura
construye `NomoWorker`; el handler no conoce ese proceso ni el proveedor del modelo.

Las sesiones retornan `CapabilityResult`, conservan la ACL existente y reciben la misma señal de cancelación.
Al liberarlas se termina el worker. El registro conserva el orden preparar → capturar → calcular embedding
→ comprobar cancelación → guardar cifrado, así como los eventos de progreso y el resultado de commit.
La prueba explícita del modelo real utiliza estos puertos; no valida micrófono ni llamadas.

### Controladores HTTP y servicios de aplicación

El BFF compone rutas versionadas con controladores separados para operaciones, eventos SSE,
dispositivos y perfiles de voz. Seguridad y traducción de errores son componentes independientes.
Los controladores interpretan solicitudes, llaman servicios y construyen respuestas; no acceden
al diario directamente. `Operations` coordina consultas, snapshots y validación del cursor.
`VoiceProfileService` valida identificadores y coordina el puerto de perfiles. Las garantías
transaccionales existentes se conservan. El encuadre SSE pertenece a presentación.

`commons/utils/` contiene el puente compartido para ejecutar trabajo bloqueante. Las utilidades
específicas permanecen en su módulo. No se crean servicios vacíos para envolver cada función.

### SOLID pragmático

Separamos por responsabilidad y motivo de cambio, sin imponer una interfaz por clase o una capa por función.
`SqlCipherJournal` conserva la propiedad de la conexión y las transacciones; delega apertura/esquema,
consultas, mutaciones, serialización, escritura de eventos, recuperación y copia diagnóstica en archivos
internos del adaptador. Las políticas de validación y finalización/cancelación viven en aplicación.
Las comprobaciones dependientes del estado almacenado permanecen dentro de la transacción; la recuperación
conserva SQL por lotes para evitar N+1. La copia diagnóstica sucede después del commit.

La consulta de dispositivos usa `DeviceCatalog` y `DeviceService`, inyectados desde bootstrap. El adaptador
CoreAudio posee la enumeración física y el controlador HTTP devuelve tipos del módulo de audio sin importar
infraestructura. Este puerto permite sustituir hardware por un catálogo controlado en pruebas del contrato.

### ACL e inversión de dependencias en cada integración

El módulo consumidor define el puerto y los tipos internos; bootstrap selecciona e inyecta el adaptador.
La implementación externa valida y traduce datos/errores mediante ACL antes de devolver Result.
Esto aplica a React, Rust y Python, incluyendo IA local/remota, HTTP, hardware y persistencia.
Las decisiones de negocio no interpretan formatos o errores de un proveedor.

Ejemplos actuales: `VoiceProfilesPort`/`HttpVoiceProfiles` con ACL de metadata; `AudioPort`/`HttpAudio`
con ACL de dispositivos; `DeviceCatalog`/`CoreAudioDeviceCatalog` convierte descripciones y errores
CPAL a tipos internos; los puertos de IA usan resultados tipados y adaptadores del proveedor.
El mapeo puede ser una función pequeña; no se exige una clase ACL ni una interfaz adicional.
Estos ejemplos no constituyen una auditoría completa de todos los límites del repositorio.

### Composición y arranque local

`bootstrap.rs` expone el arranque; sus archivos internos separan supervisor de procesos, handshake/ACL,
comandos Tauri, Keychain, composición, ejecución del servicio y drenaje al cerrar. La composición crea
los adaptadores concretos e inyecta los puertos; los comandos Tauri solo delegan.

`application/LocalHandler` despacha comandos a `VoiceRegistration` y `AudioSessions`, propietarios de sus
flujos en los módulos correspondientes. El registro recibe `AudioCapture`, `EnrollmentFactory` y
`VoiceProfiles`; la sesión recibe `AudioPlayback`, `NoiseReducerFactory` y los puertos de voz personal.
`StorageCheck` también se inyecta por abstracción. CoreAudio y RNNoise se construyen en composición.

El orden sigue siendo preparar modelo → capturar → extraer → comprobar cancelación → persistir.
La cancelación antes de persistir conserva la voz anterior. Las pruebas de estos casos usan captura/modelo
controlados y SQLCipher real; no equivalen a una prueba de micrófono ni de calidad de la IA.
