# Sprints y preparación de beta

Revisión del 20 de octubre de 2026. La implementación ya comenzó: HTTP/SSE, SQLCipher, supervisor, audio,
RNNoise, nomo-pvad, Options, Result/ACL, logs y pruebas existen. El plan anterior de 8/10–12 semanas era una
estimación inicial; no representa trabajo restante ni una fecha comprometida. Se elimina el ejemplo de fechas
porque no existe capacidad/fecha de inicio acordada para el trabajo pendiente.

Conservamos S01–S06 como identificadores de planificación. Son paquetes de trabajo con dependencias, no
sprints cerrados ni seis períodos ya calendarizados. Cadencia propuesta: iteraciones de dos semanas,
revisando cuántos tickets caben según capacidad real. Un paquete puede necesitar más de una iteración.
No se añaden bus genérico ni sagas vacías: solo coordinación que un flujo real necesite.

| Paquete                                | Situación                             | Trabajo restante / tickets         | Puerta de salida                                                                                   |
| -------------------------------------- | ------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------- |
| Base                                   | Verificada técnicamente               | T000; T001 implementado localmente | No equivale a beta; mantener pruebas y registrar commit de T001 cuando se solicite.                |
| S01 — Viabilidad física y distribución | Parcial                               | T002, T003, T004, T020             | Audio virtual real, ciclo de vida correcto y decisiones viables de consumidores/runtime/licencias. |
| S02 — Experiencia mínima y datos       | Parcial; T005 especificado            | T005, T006, T007, T015             | Panel accesible, perfiles persistidos, recuperación y Keychain probados.                           |
| S03 — Audio controlable y llamadas     | Parcial                               | T008, T009, T010, T011             | Mute real, cambios de dispositivo, comparación y matriz de llamadas aprobados.                     |
| S04 — Modelos, diagnóstico y demanda   | Parcial de infraestructura            | T014, T016, T017, T018, T021       | Gestor offline, diagnóstico, predeterminado/restauración, consumidores y CI real.                  |
| S05 — Voz personal experimental        | Modelo integrado; benchmark pendiente | T012, T013, T019                   | Consentimiento y gestión, calidad cuantificada, continuidad y estabilidad.                         |
| S06 — Distribución y aceptación        | Pendiente                             | T024, T022, T023                   | Desinstalación, instalador firmado/notarizado y QA en otro Mac.                                    |

Dependencias exactas y subtareas: [backlog.md](backlog.md). En S06, completar T024 antes de aceptar T022.
La especificación T005 puede revisarse durante S01; no bloquea las pruebas físicas. T013 puede recopilar
métricas iniciales al cerrar T003, pero su aceptación pertenece a S05. No implica personas trabajando en paralelo.

## Próxima iteración propuesta

Objetivo: demostrar audio filtrado real y conocer los dos riesgos mayores antes de ampliar UI.

1. T002: probar supervisión y salida sin huérfanos.
2. T003: recorrer micrófono → filtros → BlackHole → grabador, con permiso del usuario para capturar.
3. T004: confirmar si se pueden detectar consumidores fiablemente.
4. T020: confirmar cómo distribuir runtime/pesos/driver.
5. Revisar T005 como trabajo documental independiente, sin bloquear lo anterior.

Si la capacidad no permite los cuatro tickets técnicos en una iteración, se termina primero T002/T003 y
se replantea la siguiente. No se marca un spike como viable por tener un documento.

## Cuándo estaría lista la beta

No hay fecha defendible hasta cerrar S01 y estimar instalador/driver con evidencia. En esa revisión se
asignarán esfuerzo, capacidad, contingencia y fechas al backlog restante. Las cifras antiguas se conservan
solo como antecedente: 8 semanas para ruido y 10–12 con voz personal; no son una estimación actualizada.

- **Prueba técnica interna:** audio virtual y supervisión comprobados; puede ser manual y usar BlackHole externo. No es beta externa.
- **Beta externa de ruido:** F01–F06 y F08–F15 aceptados, incluido F13. No se exime la continuidad/detección de voz; cualquier cambio de alcance requiere acuerdo explícito.
- **Beta externa con voz personal:** además F07 y F13 aprobados experimentalmente, con límites publicados.

F12 sigue requerido: si la detección de consumidores no resulta viable, se debe acordar un cambio de alcance
antes de denominar beta a una entrega manual. Tampoco se omite el desinstalador para adelantar una fecha.

## Puertas comunes

- CI verde para arquitecturas anunciadas, sin fallos críticos conocidos; hardware Intel antes de anunciar soporte funcional.
- Evidencia de permisos, desconexión, suspensión, cierre y llamadas completas por aplicación.
- Sin captura automática tras recuperación ni procesos huérfanos al salir.
- Datos cifrados, perfiles consistentes y recuperación sin sobrescribir DB/clave.
- Distribución de modelos/driver resuelta, instalación y eliminación verificadas.
- Sin login, sin envío de audio a red, sin voz ni secretos en logs; la descarga explícita de modelos es un flujo separado.
- Firma/notarización y prueba en otro Mac para beta externa; un artefacto CI sin firma no basta.

Cloud y Windows no tienen fecha ni tickets de implementación en este backlog. La UI/UX se especifica en
[ui-ux.md](ui-ux.md); su diseño no acredita implementación ni aprobación visual del usuario.
