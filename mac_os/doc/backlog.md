# Tickets y tareas — beta Local

Corte: 20 de octubre de 2026. Registro local versionado; **no se crearon issues remotos**.
T000 es base técnica verificada, T001 está implementado localmente y T005 entrega especificación.
Los demás tickets siguen pendientes aunque reutilicen código existente. Ninguno sustituye la aceptación F01–F15.
Responsables aún sin asignar. P0 bloquea calidad/viabilidad/salida; P1 completa experiencia requerida, no es opcional.
Las dependencias se satisfacen con aceptación del ticket, no con su mera implementación.

## Tablero

| Ticket        | Entrega                                                      | Función            | Sprint | Prioridad | Estado                                  | Depende de                   |
| ------------- | ------------------------------------------------------------ | ------------------ | ------ | --------- | --------------------------------------- | ---------------------------- |
| [T000](#t000) | Base técnica existente                                       | Transversal        | Base   | P0        | Verificado técnicamente                 | —                            |
| [T001](#t001) | Inyección de registro y filtro de voz                        | F07                | Base   | P0        | Implementado local; sin commit          | T000                         |
| [T002](#t002) | Ciclo de vida del servicio y sus workers                     | F02, F12           | S01    | P0        | Pendiente                               | T000                         |
| [T003](#t003) | Primer recorrido real micrófono → BlackHole                  | F04, F05           | S01    | P0        | Pendiente                               | T002                         |
| [T004](#t004) | Spike de detección de consumidores y distribución del driver | F12, F14           | S01    | P0        | Pendiente                               | T003                         |
| [T005](#t005) | Estándares visuales y estados de producto                    | F01, F10           | S02    | P1        | Especificado; revisión visual pendiente | T000                         |
| [T006](#t006) | Barra de menús y panel compacto                              | F01                | S02    | P1        | Pendiente                               | T005, T002                   |
| [T007](#t007) | Perfiles de ajustes cifrados                                 | F03, F09           | S02    | P1        | Pendiente                               | T000                         |
| [T008](#t008) | Mute/reanudación del flujo controlado                        | F04                | S03    | P0        | Pendiente                               | T003                         |
| [T009](#t009) | Capacidades y cambio de dispositivo                          | F04                | S03    | P1        | Pendiente                               | T003, T008                   |
| [T010](#t010) | Matriz de llamadas reales                                    | F05, F11           | S03    | P0        | Pendiente                               | T003, T008                   |
| [T011](#t011) | Control de ruido y comparación A/B                           | F06                | S03    | P1        | Pendiente                               | T003                         |
| [T012](#t012) | Consentimiento y gestión del perfil personal                 | F07                | S05    | P1        | Pendiente                               | T001, T007                   |
| [T013](#t013) | Benchmark de voz personal                                    | F07, F13           | S05    | P0        | Pendiente                               | T003, T001                   |
| [T014](#t014) | Gestor de modelos dentro de la app                           | F08                | S04    | P0        | Pendiente                               | T020, T000                   |
| [T015](#t015) | Keychain y recuperación de datos en Mac                      | F09                | S02    | P0        | Pendiente                               | T007                         |
| [T016](#t016) | Diagnóstico integral y métricas                              | F10                | S04    | P1        | Pendiente                               | T003, T000                   |
| [T017](#t017) | Predeterminado del sistema y restauración                    | F11                | S04    | P1        | Pendiente                               | T010                         |
| [T018](#t018) | Activación automática por consumidor                         | F12                | S04    | P0        | Pendiente                               | T004, T010                   |
| [T019](#t019) | Continuidad de voz y estabilidad                             | F13                | S05    | P0        | Pendiente                               | T013, T009                   |
| [T020](#t020) | Spike de empaquetado y licencias                             | F08, F14           | S01    | P0        | Pendiente                               | T000                         |
| [T021](#t021) | CI y artefactos reproducibles                                | F14                | S04    | P0        | Pendiente                               | T020                         |
| [T022](#t022) | Instalador firmado y notarizado                              | F14                | S06    | P0        | Pendiente                               | T014, T020, T021, T024       |
| [T023](#t023) | QA de UI y accesibilidad                                     | F01, F04, F07, F10 | S06    | P1        | Pendiente                               | T006, T008, T012, T014, T016 |
| [T024](#t024) | Desinstalación y recuperación                                | F15                | S06    | P0        | Pendiente                               | T020, T007, T015             |

## Criterio común de cierre

Contrato revisado antes de cambios incompatibles; implementación bajo puertos/adaptadores, pruebas pertinentes,
formato/lint/tipos/build según lenguaje y evidencia enlazada al ticket. Cifrado, SQL parametrizado y consultas
sin N+1; ninguna muestra privada ni secreto en Git/logs. UI y pruebas simuladas no prueban hardware.
Los cambios de alcance (driver propio, comportamiento de perfiles, distribución) requieren decisión explícita.
Cada cierre registrará commit, comando/versión de entorno, resultado y limitaciones; PR/CI si corresponde.

<a id="t000"></a>

## T000 — Base técnica existente

Función: Transversal. Sprint: Base. Prioridad: P0. Dependencias: —.

- [x] **T000.01** — Conservar HTTP/SSE, SQLCipher, Options, Result/ACL y retención de logs.
- [x] **T000.02** — Mantener suites por módulo y runner central.

**Aceptación:** Pruebas y build locales documentados; no equivale a beta ni CI remoto.

**Evidencia:** [validación existente](validation.md); para T001, ejecución posterior de 19 tests Rust y una prueba real del modelo por los nuevos puertos.

<a id="t001"></a>

## T001 — Inyección de registro y filtro de voz

Función: F07. Sprint: Base. Prioridad: P0. Dependencias: T000.

- [x] **T001.01** — Introducir EnrollmentFactory/EnrollmentSession y PersonalVoiceFactory.
- [x] **T001.02** — Componer NomoFactory desde bootstrap sin NomoWorker en LocalHandler.
- [x] **T001.03** — Ejecutar registro/filtro y cancelación por puertos con modelo real.

**Aceptación:** 19 tests Rust normales y prueba real adicional aprobados; conservar orden de captura y guardado.

**Evidencia:** [validación existente](validation.md); para T001, ejecución posterior de 19 tests Rust y una prueba real del modelo por los nuevos puertos.

<a id="t002"></a>

## T002 — Ciclo de vida del servicio y sus workers

Función: F02, F12. Sprint: S01. Prioridad: P0. Dependencias: T000.

- [ ] **T002.01** — Probar cerrar, ocultar, salida explícita, crash del host y arranque duplicado.
- [ ] **T002.02** — Registrar procesos antes/después, stdin/EOF y duración de cierre.
- [ ] **T002.03** — Corregir huérfanos y probar reinicio sin reanudar captura.

**Aceptación:** No queda servicio ni Python capturando tras salir o perder el host; evidencia en Mac.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t003"></a>

## T003 — Primer recorrido real micrófono → BlackHole

Función: F04, F05. Sprint: S01. Prioridad: P0. Dependencias: T002.

- [ ] **T003.01** — Preparar BlackHole externo de desarrollo y permisos con consentimiento.
- [ ] **T003.02** — Capturar señal controlada y verificar salida en un grabador sin bucle.
- [ ] **T003.03** — Probar parada, formato no soportado, pérdida de entrada y error de salida.

**Aceptación:** Archivo de medición autorizado y registro de dispositivos/formatos prueban audio recibido; sin grabaciones privadas en Git.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t004"></a>

## T004 — Spike de detección de consumidores y distribución del driver

Función: F12, F14. Sprint: S01. Prioridad: P0. Dependencias: T003.

- [ ] **T004.01** — Investigar señal observable del driver y distinguir productor de consumidor.
- [ ] **T004.02** — Probar cero, uno y dos consumidores, pestañas y cierres inesperados.
- [ ] **T004.03** — Documentar viabilidad, licencia/distribución y alternativas con costes.

**Aceptación:** Decisión técnica con evidencia. Si no hay señal fiable, F12 bloqueado; no sustituirlo silenciosamente por activación manual.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t005"></a>

## T005 — Estándares visuales y estados de producto

Función: F01, F10. Sprint: S02. Prioridad: P1. Dependencias: T000.

- [x] **T005.01** — Definir referencias, temas, tokens y componentes accesibles.
- [x] **T005.02** — Especificar panel compacto, ajustes, onboarding y registro.
- [ ] **T005.03** — Revisar dirección visual con el usuario antes de aplicar el estilo a producción.

**Aceptación:** Especificación y tokens documentados; contraste calculado. Aún no implica UI implementada ni preferencia visual aprobada.

**Evidencia:** [especificación](ui-ux.md), [tokens](design-tokens.json) y [contraste](design-contrast.md); sin UI aplicada.

<a id="t006"></a>

## T006 — Barra de menús y panel compacto

Función: F01. Sprint: S02. Prioridad: P1. Dependencias: T005, T002.

- [ ] **T006.01** — Añadir icono nativo y ventana anclada con límites de pantalla.
- [ ] **T006.02** — Implementar Escape, clic fuera, restauración de foco y separación ocultar/salir.
- [ ] **T006.03** — Enlazar controles existentes a sus estados reales, sin medidores simulados.

**Aceptación:** Panel operable por teclado/VoiceOver, no cortado con escalado, y salir termina servicio.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t007"></a>

## T007 — Perfiles de ajustes cifrados

Función: F03, F09. Sprint: S02. Prioridad: P1. Dependencias: T000.

- [ ] **T007.01** — Definir plantillas Reuniones/Entorno ruidoso/Grabación, creación personalizada y relación opcional a voz; acordar cambio/eliminación del activo antes de migrar.
- [ ] **T007.02** — Implementar múltiples perfiles por persona: crear desde plantilla o personalizado, editar copias, duplicar, seleccionar y eliminar; puertos y SQL parametrizado.
- [ ] **T007.03** — Probar reinicio, actualización de plantillas sin sobrescribir copias, referencia ausente, perfil activo y listados por lotes.

**Aceptación:** CRUD sin login conserva varios perfiles; plantillas de fábrica y copias personalizadas diferenciadas; selección no inicia captura. Referencia a voz consistente, sin N+1 ni pérdida de datos. Ver [perfiles](profiles.md).

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t008"></a>

## T008 — Mute/reanudación del flujo controlado

Función: F04. Sprint: S03. Prioridad: P0. Dependencias: T003.

- [ ] **T008.01** — Definir comando y estado distintos de cancelar sesión.
- [ ] **T008.02** — Vaciar/invalidar bloques pendientes y confirmar silencio antes de mostrar Silenciado.
- [ ] **T008.03** — Probar reanudación, carreras con cancelación y pérdida de dispositivo.

**Aceptación:** Salida virtual en silencio comprobado, sin audio antiguo al reanudar; no altera micrófonos ajenos.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t009"></a>

## T009 — Capacidades y cambio de dispositivo

Función: F04. Sprint: S03. Prioridad: P1. Dependencias: T003, T008.

- [ ] **T009.01** — Exponer frecuencias/canales/formatos realmente soportados y motivo de incompatibilidad.
- [ ] **T009.02** — Definir cambio de entrada durante sesión y recuperación explícita.
- [ ] **T009.03** — Probar interno/USB/Bluetooth, desconexión y suspensión.

**Aceptación:** Cambio seguro sin reiniciar captura automáticamente ni simular éxito; formatos no soportados explicados.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t010"></a>

## T010 — Matriz de llamadas reales

Función: F05, F11. Sprint: S03. Prioridad: P0. Dependencias: T003, T008.

- [ ] **T010.01** — Probar Teams, Zoom, Meet y Slack con versión/SO/dispositivo anotados.
- [ ] **T010.02** — Verificar selección virtual, mute, cierre/reapertura y consumo simultáneo.
- [ ] **T010.03** — Registrar latencia, feedback, cortes y resultados por aplicación.

**Aceptación:** Cada aplicación anunciada tiene evidencia de audio recibido; una falla impide anunciar esa compatibilidad.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t011"></a>

## T011 — Control de ruido y comparación A/B

Función: F06. Sprint: S03. Prioridad: P1. Dependencias: T003.

- [ ] **T011.01** — Implementar bypass explícito de RNNoise sin cambiar dispositivo.
- [ ] **T011.02** — Añadir prueba de audio voluntaria con muestra temporal y borrado definido.
- [ ] **T011.03** — Medir original/filtrado, CPU/RAM y latencia en M2 y batería.

**Aceptación:** Comparación reproducible, controles confirmados por backend y presupuesto de rendimiento revisado.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t012"></a>

## T012 — Consentimiento y gestión del perfil personal

Función: F07. Sprint: S05. Prioridad: P1. Dependencias: T001, T007.

- [ ] **T012.01** — Diseñar paso previo al registro explicando duración, uso en RAM y embedding cifrado.
- [ ] **T012.02** — Permitir cancelar, reemplazar y eliminar perfil con efectos claros.
- [ ] **T012.03** — Verificar muestra temporal no persistida y estado tras cancelación tardía.

**Aceptación:** Usuario decide registrar; no se confunde ajustes con perfil de voz; borrado elimina referencia y embedding correcto.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t013"></a>

## T013 — Benchmark de voz personal

Función: F07, F13. Sprint: S05. Prioridad: P0. Dependencias: T003, T001.

- [ ] **T013.01** — Definir corpus consentido/licenciado con voz objetivo, ajena, ruido y superposición.
- [ ] **T013.02** — Fijar antes del ensayo umbrales de aceptación/rechazo y latencia.
- [ ] **T013.03** — Medir resultados, calibrar threshold y decidir inclusión experimental.

**Aceptación:** Informe reproducible con fallos y límites; no anunciar Solo mi voz aceptado por ejecutar el modelo.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t014"></a>

## T014 — Gestor de modelos dentro de la app

Función: F08. Sprint: S04. Prioridad: P0. Dependencias: T020, T000.

- [ ] **T014.01** — Mostrar capacidad, versión, tamaño, licencia y descarga explícita.
- [ ] **T014.02** — Implementar staging, hash, progreso, cancelación, recuperación y eliminación idempotente.
- [ ] **T014.03** — Probar falta de espacio, hash incorrecto, red cortada e inferencia sin red.

**Aceptación:** Modelo disponible solo tras validación completa; UI no inventa porcentajes ni activación prematura.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t015"></a>

## T015 — Keychain y recuperación de datos en Mac

Función: F09. Sprint: S02. Prioridad: P0. Dependencias: T007.

- [ ] **T015.01** — Probar permiso denegado, clave ausente con DB existente y clave incorrecta.
- [ ] **T015.02** — Documentar recuperación/conservación coherente de DB y clave.
- [ ] **T015.03** — Probar WAL, reinicio, cambio de versión y copias sin exponer datos.

**Aceptación:** Nunca reemplaza clave/DB para ocultar errores; diagnóstico recuperable y evidencia de cifrado.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t016"></a>

## T016 — Diagnóstico integral y métricas

Función: F10. Sprint: S04. Prioridad: P1. Dependencias: T003, T000.

- [ ] **T016.01** — Añadir estado de modelo/entrada/salida y contadores de underrun/overrun fuera del callback.
- [ ] **T016.02** — Presentar latencia/recursos solo con fuente y unidad; ausencia como No disponible.
- [ ] **T016.03** — Probar logs privados, retención, copia de eventos y exportación saneada si se incorpora.

**Aceptación:** Errores guían a una acción; no audio/embeddings/secrets en diagnóstico; métricas no inventadas.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t017"></a>

## T017 — Predeterminado del sistema y restauración

Función: F11. Sprint: S04. Prioridad: P1. Dependencias: T010.

- [ ] **T017.01** — Solicitar cambio explícito y conservar identificación del dispositivo anterior.
- [ ] **T017.02** — Implementar restauración si existe y alternativa si desapareció.
- [ ] **T017.03** — Probar aplicaciones con entrada fija y predeterminada por separado.

**Aceptación:** No cambia dispositivos al arrancar ni promete controlar todas las apps; restaura sin afectar elecciones posteriores del usuario.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t018"></a>

## T018 — Activación automática por consumidor

Función: F12. Sprint: S04. Prioridad: P0. Dependencias: T004, T010.

- [ ] **T018.01** — Implementar adaptador de consumidores según decisión del spike.
- [ ] **T018.02** — Activar al primero, mantener con varios y liberar al último con política definida.
- [ ] **T018.03** — Probar carreras, productor solo, permisos y cierre abrupto.

**Aceptación:** Captura/inferencia verificadas en reposo sin consumidores; si spike falla, ticket bloqueado y criterio de beta no cumplido.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t019"></a>

## T019 — Continuidad de voz y estabilidad

Función: F13. Sprint: S05. Prioridad: P0. Dependencias: T013, T009.

- [ ] **T019.01** — Medir primeras sílabas, pausas, voz débil y retorno tras silencio.
- [ ] **T019.02** — Evaluar buffering/histéresis solo si la medición lo requiere.
- [ ] **T019.03** — Ejecutar dos horas, suspensión/reanudación y cambios de reloj/dispositivo.

**Aceptación:** Sin crecimiento sostenido ni pérdidas fuera del presupuesto acordado; límites documentados con métricas.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t020"></a>

## T020 — Spike de empaquetado y licencias

Función: F08, F14. Sprint: S01. Prioridad: P0. Dependencias: T000.

- [ ] **T020.01** — Inventariar runtime Python, pesos, RNNoise y driver con versiones/licencias.
- [ ] **T020.02** — Probar runtime redistribuible sin Python/globales del desarrollador.
- [ ] **T020.03** — Determinar tamaño, firma, permisos/auxiliar y suministro de pesos.

**Aceptación:** Ruta de distribución documentada y viable; no tratar el venv de desarrollo como runtime instalable.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t021"></a>

## T021 — CI y artefactos reproducibles

Función: F14. Sprint: S04. Prioridad: P0. Dependencias: T020.

- [ ] **T021.01** — Ejecutar workflow real sobre el commit previsto y revisar logs.
- [ ] **T021.02** — Validar runners/arquitecturas, locks, suites y contenido del bundle.
- [ ] **T021.03** — Publicar evidencia de build; separar artefactos sin firma de releases.

**Aceptación:** CI verde en arquitecturas anunciadas y artefactos inspeccionados; Intel requiere también hardware para soporte funcional.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t022"></a>

## T022 — Instalador firmado y notarizado

Función: F14. Sprint: S06. Prioridad: P0. Dependencias: T014, T020, T021, T024.

- [ ] **T022.01** — Construir instalador con inventario de componentes y hashes.
- [ ] **T022.02** — Firmar/notarizar y comprobar Gatekeeper, actualización y fallo intermedio.
- [ ] **T022.03** — Instalar en otro Mac sin herramientas de desarrollo y probar offline.

**Aceptación:** Instalación/reinstalación funcional con modelos seleccionados; credenciales de firma solo en entorno seguro.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t023"></a>

## T023 — QA de UI y accesibilidad

Función: F01, F04, F07, F10. Sprint: S06. Prioridad: P1. Dependencias: T006, T008, T012, T014, T016.

- [ ] **T023.01** — Probar todos los estados y errores de ui-ux.md con backend real.
- [ ] **T023.02** — Verificar VoiceOver, teclado, foco, contraste, texto largo y temas.
- [ ] **T023.03** — Corregir recortes y estados optimistas que contradigan servicio.

**Aceptación:** Recorrido completo sin éxito simulado; evidencias visuales y accesibilidad por estado.

**Evidencia:** pendiente; adjuntar resultados al cerrar.

<a id="t024"></a>

## T024 — Desinstalación y recuperación

Función: F15. Sprint: S06. Prioridad: P0. Dependencias: T020, T007, T015.

- [ ] **T024.01** — Definir inventario, selección conservar/eliminar y auxiliar final si es necesario.
- [ ] **T024.02** — Cerrar procesos, eliminar componentes propios y preservar dependencias compartidas.
- [ ] **T024.03** — Probar permisos denegados, limpieza parcial, reinstalación y acceso sin UI funcional.

**Aceptación:** Desinstalación verificable en Mac limpio; conservación coherente de DB/clave y ningún borrado ajeno.

**Evidencia:** pendiente; adjuntar resultados al cerrar.
