# Plan de pruebas

## Situación actual

Existen suites Rust de operaciones, persistencia, transporte y procesamiento, pruebas Node del parser SSE y un smoke test del runtime personal. Su existencia no acredita compatibilidad física ni precisión de reconocimiento. La estructura implementada está en [convenciones de arquitectura](architecture-conventions.md#pruebas-por-módulo-y-entrada-central).

## Matriz

| Nivel              | Casos relevantes                                                                    | Evidencia                                                                   |
| ------------------ | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Dominio/aplicación | Invariantes de perfiles, selección de modelos, cancelación y compensaciones         | Tests deterministas al implementar casos de uso.                            |
| Contratos          | Envelope/eventos, versiones IPC, mensajes truncados, tamaño máximo, correlación     | Fixtures serializables y pruebas entre frontend/host/servicio.              |
| Eventos/sagas      | Duplicados, fallos de handlers, orden por sesión, colas llenas y reanudación        | Integración con bus real y almacenamiento temporal.                         |
| Ciclo de vida      | Salir, ocultar, doble arranque, crash del padre, crash del hijo, restart            | Pruebas de procesos y verificación de que termina la captura.               |
| Persistencia       | Migración, lock, clave ausente/incorrecta, Keychain denegado, backup y recuperación | Integración SQLCipher; comprobar datos no legibles en DB/WAL/exportaciones. |
| Audio offline      | Silencio, ruido, clipping, cambio de frecuencia, voz objetivo y ajena               | Fixtures consentidas o licenciadas; resultado y tiempo medidos.             |
| Hardware           | Interno, USB, Bluetooth, desconexión, suspensión, cambio de entrada                 | QA manual en Mac real, no simulado en CI.                                   |
| UX                 | Escape, foco, navegación teclado, estado sin color, carga y errores                 | Pruebas de componentes y recorrido manual del panel.                        |
| Distribución       | Instalar, abrir, permisos, driver, eliminar, actualizar                             | Otro Mac limpio, app firmada y notarizada.                                  |

## Objetivos provisionales de rendimiento

Medir primero en M2/16 GB, adaptador de corriente y batería, con formato y dispositivo registrados. Objetivos iniciales, no capacidades demostradas: retraso añadido p95 de hasta 80 ms en modo ruido y hasta 300 ms en voz personal; CPU media menor al 15% del equipo normalizada por todos los núcleos, memoria residente total de frontend+host+servicio menor a 1 GB en ruido y 2 GB con runtime personal. Los umbrales se revisan con el spike, sin redefinirlos silenciosamente para aprobar.

Sesión continua de dos horas sin crash ni crecimiento sostenido de memoria; contar underruns/overruns. Medir energía e impacto en batería por separado. Para voz personal medir aceptación falsa y rechazo falso en un conjunto consentido con voces/distancias/dispositivos distintos; S01 fijará umbrales y conjunto antes de aceptar F07. Incluir habla superpuesta y reportar el límite del modelo aunque las demás pruebas pasen.

Confirmar entrega del audio en Teams, Zoom, Google Meet, Slack y OBS seleccionando la entrada virtual; silenciar la app no debe confundirse con revocar permisos ni silenciar todos los micrófonos del sistema. Después de salir, otra aplicación podría seguir accediendo a su micrófono físico: el producto controla su propio pipeline.

## Comandos actuales

```bash
pnpm install --frozen-lockfile
pnpm run format:check
pnpm run lint
pnpm run typecheck
pnpm test
pnpm test lifecycle # macOS: procesos reales, Keychain y loopback; sin micrófono
pnpm run test:models # explícito: requiere runtime privado instalado
pnpm run build
pnpm run security:audit
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo clippy --locked --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings
cargo test --locked --manifest-path src-tauri/Cargo.toml
```

Las pruebas Node actuales cubren el parser SSE, no la interfaz completa. No ejecutar `--passWithNoTests` para presentar cobertura. La compilación en CI no valida modelos, hardware ni permisos de captura.

Pruebas de demanda: abrir una llamada, abrir dos a la vez, cerrar una y luego la última; verificar que la captura solo entra en reposo al finalizar la última. Probar navegador con varias pestañas, permisos denegados, productor virtual activo sin consumidores, inicio frío del modelo, primera sílaba, silencios prolongados y cierre inesperado de la app consumidora. Comprobar captura/inferencia por métricas y actividad del dispositivo; no deducirlas del icono de la UI.

Registrar versión de app y navegador, dispositivo, frecuencia de muestreo y formato en cada prueba de compatibilidad. Probar selección explícita y predeterminado del sistema por separado. No afirmar soporte por el simple hecho de listar el micrófono virtual.

La matriz de instalación/desinstalación de [installation.md](installation.md) es obligatoria antes de beta externa, incluyendo conservación de DB y clave juntas, driver compartido, permisos denegados, limpieza parcial y reinstalación.

Validar HTTP/SSE y los límites de audio descritos en [audio-transport.md](audio-transport.md), incluyendo cancelación con datos en vuelo. gRPC solo requiere pruebas si un adaptador concreto lo incorpora; no es el transporte general de control.

## Supervisión T002

Las pruebas de supervisor viven en `src-tauri/src/bootstrap/test/`, coordinadas por `test/rust.rs` y
`test/run.mjs`. La suite optativa `lifecycle` compila el binario y prueba handshake ausente, instancia duplicada,
EOF, reinicio y muerte del supervisor de servicio/worker real. Requiere el runtime privado instalado y acceso
al Keychain local; usa bases temporales, no reemplaza la base del usuario ni imprime claves/tokens.
Las pruebas normales usan un proceso simple solo para verificar espera cooperativa y fallback forzado;
no se presentan como evidencia de IA ni de captura. La liberación del micrófono se verifica en T003.

## Medición optativa de BlackHole

`pnpm test audio-hardware --seconds 8 --expect silence` recibe PCM de BlackHole sin guardar audio.
Con la sesión iniciada: `pnpm test audio-hardware --seconds 12 --speak --expect signal` reproduce una frase
sintética por la salida actual y mide la señal recibida. Requiere ffmpeg instalado por separado y permiso de
micrófono; no forma parte de CI ni se ejecuta en la suite normal. No cambiar la salida predeterminada a
BlackHole para esta prueba. El conteo prueba recepción, no calidad, latencia ni ausencia de frames perdidos.

## Arquitectura y vistas

`pnpm run lint` comprueba que las vistas TSX delegan estado, efectos, decisiones y handlers en hooks/funciones,
y que aplicación/dominio frontend no importan infraestructura ni presentación. Las listas y condiciones de
visibilidad sobre estados preparados siguen siendo JSX declarativo. `main.tsx` es la entrada de composición.

La suite central incluye pruebas puras del pipeline, registro con captura inyectada, ACL de conexión/eventos,
selección de perfiles y transporte Python con streams controlados. Esas pruebas no abren micrófonos y no
sustituyen T003 ni el benchmark de voz. Ver [revisión SOLID/ACL](solid-acl-review.md).

## Spikes opt-in S01

- `pnpm test audio-consumers --producer-pid <pid> --device-id <id>`: compila el sondeo CoreAudio,
  exige productor activo y abre/cierra dos receptores FFmpeg de BlackHole sin guardar PCM.
  Falla ante estado desconocido o productor detenido. No demuestra equivalencia entre PID y pestaña.
- `pnpm test driver-spike --source <BlackHole.c>`: exige hash de la fuente 0.7.1 y prueba
  contadores de dispositivos separados dentro de un proceso. No instala un driver.
- La suite Rust incluye rechazo de formatos, señales de fallo de captura/salida, backpressure
  y persistencia de errores. Son pruebas controladas; no equivalen a desconexión física.

Resultados reales, limitaciones y autonomía del runtime: [s01-validation.md](s01-validation.md).
