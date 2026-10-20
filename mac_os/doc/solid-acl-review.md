# Revisión de SOLID, código limpio y ACL

20 de octubre de 2026. Alcance: fuentes de la edición Local en `src/`, `src-tauri/src/`, runtime Python,
composición y sus pruebas. Refactorización posterior a `d02fa1f`; no modifica el alcance de la beta.
Se revisaron imports entre capas, construcción de adaptadores, vistas, contratos y límites externos.
No se considera que dividir archivos por sí solo garantice SOLID.

## Hallazgos y cambios

| Área          | Hallazgo                                                                      | Corrección aplicada                                                                                                                |
| ------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Arranque      | Supervisor, Tauri, Keychain, composición y casos de uso juntos                | Archivos separados; bootstrap compone adaptadores, LocalHandler despacha a servicios del módulo                                    |
| Audio         | Controlador y casos de uso accedían a CoreAudio/RNNoise concretos             | Puertos de catálogo, captura, reproducción y creación del reductor; DI desde composición                                           |
| Procesamiento | Captura, callback de salida y política de filtrado dentro del mismo adaptador | CoreAudio separado en configuración/captura/salida; AudioPipeline independiente del hardware; remuestreo puro en dominio           |
| Operaciones   | Validación, SQL, eventos, recuperación y copia a logs mezclados               | Políticas en aplicación; adaptador con archivos internos por responsabilidad y una transacción propietaria                         |
| Voces         | Migración, catálogo, escritura y descodificación en un archivo                | Adaptador separado; ACL de embeddings y guardia transaccional explícita                                                            |
| Worker Rust   | Gestión del proceso interpretaba también respuestas del modelo                | ACL de protocolo separada de ejecución/tiempos de espera; errores internos tipados                                                 |
| Python        | Protocolo dependía de stdin/stdout globales                                   | Transporte recibe streams y puerto de IA; worker queda como composición y supervisión                                              |
| React         | Casts de handshake/SSE, adaptación cruzada y hook de catálogo mezclado        | Validación de respuestas desconocidas, proyección de campos admitidos, contrato público de operaciones y hooks por responsabilidad |
| Vistas        | Condiciones derivadas y acceso a estructura del modal en JSX                  | Flags y nombre preparados; diálogo separado; funciones para selección, solicitud y mensajes                                        |
| Commons       | Errores, comandos, conexión, entorno, retención y transporte Tauri mezclados  | Archivos por responsabilidad; conversión de errores SQLite en infraestructura compartida                                           |

## Dependencias y límites

- Aplicación y dominio Rust no importan CPAL, SQLCipher/rusqlite, Tauri ni implementaciones de infraestructura.
- Vistas React consumen hooks; los hooks coordinan puertos. Solo representación declarativa en JSX.
- ESLint impide estado/efectos/IO, decisiones imperativas, ternarios y handlers inline en vistas, y bloquea
  imports de infraestructura/presentación desde aplicación/dominio. Una prueba por stdin confirmó el rechazo
  de una vista con `useState` e `if`, sin crear un archivo de producto.
- La composición conoce adaptadores concretos: esa dependencia es intencional. No se crea una interfaz por
  función auxiliar ni un Strategy para reemplazar una selección simple.
- HTTP, SSE, CPAL, el worker y los modelos permanecen detrás de adaptadores; sus datos/errores se convierten
  a tipos internos. El handshake acepta solo loopback y una versión válida; SSE valida su correlación y elimina
  campos externos no declarados.
- La guardia de escritura de voces consulta el diario dentro de la misma transacción SQLCipher. Se preserva
  esa coordinación del monolito para no abrir carreras con captura activa. No se anuncia independencia física
  de las bases de cada módulo ni extracción a servidores ya resuelta.

## Contratos preservados

Rutas y valores serializados, nombres de comandos Tauri, opciones existentes, esquema cifrado, exclusión de
sesiones y eventos permanecen compatibles. El registro prepara el modelo antes de capturar; cancelar antes
del guardado conserva la voz previa. La recuperación mantiene SQL por lotes y la copia de logs ocurre tras
confirmar la transacción. La ACL rechaza respuestas malformadas; eso no cambia un contrato válido.

## Verificación

- 37 pruebas Rust normales aprobadas, incluyendo pipeline con y sin voz, cancelación durante inferencia,
  captura inyectada, conservación del perfil al fallar y cancelación tardía después de persistir.
- 14 pruebas frontend y 6 Python aprobadas: selección, metadata, SSE, errores y transporte acotado.
- Prueba adicional con nomo-pvad/embedding real aprobada usando el runtime instalado; sin micrófono.
- Suite de procesos aprobada: handshake ausente, instancia duplicada, EOF, reinicio, muerte de supervisor y
  muerte del padre del worker cargado o cargando. Usa procesos reales y almacenamiento temporal.
- Lint, tipos, build React, Clippy, rustfmt, Ruff y Prettier aprobados en esta revisión.
- Bundle Tauri debug generado: 46.54 MiB; 7 recursos de runtime cotejados con los fuentes, incluido
  `transport/personal_voice.py`. Es un bundle de desarrollo, no un instalador firmado/notarizado.
- UI del bundle actualizado: servicio conectado, predeterminada visible, modal de reemplazo y Escape,
  modal de eliminación y Volver; perfil conservado. No se confirmó reemplazo ni borrado.
- Diagnóstico real desde UI completado mediante HTTP/SSE, operación `c31d3e1d-3953-410b-87dc-17df87545c76`.
  No se inició captura en esta revisión visual.

Estas pruebas no sustituyen llamadas reales, calidad/latencia ni QA visual. T002/T003 conservan pendientes de
registro/interrupción con micrófono activo y fallos de dispositivos; T004/T020 siguen abiertos.
