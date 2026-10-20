# Funcionalidades de la beta Local

Estado revisado el 20 de octubre de 2026 contra código y pruebas locales. Hay implementación parcial;
ninguna función F01–F15 está aceptada todavía como beta. «Parcial» no acredita hardware, calidad ni distribución.
La última inyección de registro/filtro está implementada localmente y aún no está en un commit.

## Estado y trabajo restante

| ID  | Estado                          | Evidencia existente                                                                                           | Pendiente para aceptación                                                      | Tickets          |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------- |
| F01 | Parcial                         | Ventana React con controles y operaciones.                                                                    | Barra, popover, Escape, clic fuera, foco y accesibilidad.                      | T005, T006, T023 |
| F02 | Implementado; falta QA integral | Supervisor, handshake, bloqueo y EOF del padre.                                                               | Cierre, caída, arranque duplicado y workers sin huérfanos.                     | T002             |
| F03 | Pendiente                       | Perfil de voz único; no equivale a perfiles de ajustes.                                                       | CRUD, duplicar, seleccionar, referencias y recuperación.                       | T007             |
| F04 | Parcial                         | Entradas reales, captura y cancelación.                                                                       | Capacidades visibles, mute/reanudación y reconexión física.                    | T008, T009       |
| F05 | Parcial                         | Salida CPAL a BlackHole 2ch; excluye BlackHole como captura.                                                  | Audio recibido sin realimentación en una llamada.                              | T003, T010       |
| F06 | Parcial                         | RNNoise y tests con PCM sintético.                                                                            | Bypass, comparación A/B y benchmark de ruido/recursos.                         | T011             |
| F07 | Parcial experimental            | Registro en RAM, embedding cifrado, nomo-pvad, ACL, Result e inyección; prueba real del modelo sin micrófono. | Consentimiento, gestión del perfil y benchmark de voces.                       | T001, T012, T013 |
| F08 | Parcial de desarrollo           | Script privado con manifiesto, versiones, tamaños y hashes.                                                   | Gestor en app: progreso, cancelación, eliminación y offline.                   | T014             |
| F09 | Parcial                         | SQLCipher y recuperación probados; Keychain integrado.                                                        | Ajustes cifrados, denegación/pérdida de clave y recuperación en Mac.           | T007, T015       |
| F10 | Parcial                         | Integridad, operaciones, errores, logs/copia de eventos y limpieza temporal probados.                         | Métricas, diagnóstico integral y presentación accionable.                      | T016             |
| F11 | Parcial                         | Adaptador BlackHole; sin compatibilidad de llamadas demostrada.                                               | Matriz Teams/Zoom/Meet/Slack y predeterminado/restauración.                    | T010, T017       |
| F12 | Parcial                         | Servicio ligado al host; activación manual.                                                                   | Detectar consumidores de forma fiable y gestionar reposo.                      | T002, T004, T018 |
| F13 | Parcial                         | Gate por probabilidad en sesión continua.                                                                     | Primeras sílabas, silencios, voces ajenas y latencia.                          | T013, T019       |
| F14 | Parcial de build                | Bundle .app generado; workflow definido.                                                                      | Runtimes/pesos/driver distribuibles, firma, notarización y Mac limpio.         | T020, T021, T022 |
| F15 | Pendiente                       | Estrategia documentada.                                                                                       | Desinstalación, conservación de datos, recuperación y componentes compartidos. | T024             |

Los tickets y subtareas están en [backlog.md](backlog.md); las dependencias y puertas en [sprints.md](sprints.md).
Evidencia técnica: [validación](validation.md), [control HTTP/SSE](control.md),
[contratos de voz](../src-tauri/src/modules/personal_voice/application/enrollment.rs),
[audio](../src-tauri/src/modules/audio/infrastructure/core_audio.rs) y [tests](../test/README.md).

## Criterios de aceptación conservados

| ID  | Función                  | Aceptación                                                                                                                                               |
| --- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F01 | Barra de menús y panel   | Estado legible sin depender del color; Escape y clic fuera ocultan el panel; salir termina el servicio.                                                  |
| F02 | Servicio supervisado     | No arranca sin app; handshake versionado, una instancia por usuario y salida al perder supervisor.                                                       |
| F03 | Perfiles configurables   | Crear, editar, duplicar, seleccionar y eliminar ajustes locales; sin login. Un perfil de ajustes referencia opcionalmente un perfil de voz.              |
| F04 | Micrófono y mute         | Listar entradas reales, mostrar capacidades y silenciar el flujo controlado. No afirmar que se silenciaron entradas físicas ajenas.                      |
| F05 | Salida virtual           | El usuario selecciona la entrada virtual en la app de llamada; el audio filtrado llega y no produce realimentación.                                      |
| F06 | Ruido                    | Activar/desactivar el motor elegido; comparación con señal original y medición de coste.                                                                 |
| F07 | Solo mi voz experimental | Registrar muestra con consentimiento local, eliminarla tras extraer el perfil y mostrar límites conocidos. No prometer separación de voces superpuestas. |
| F08 | Gestión de modelos       | Descarga inicial explícita, progreso, tamaño real, versión, hash, cancelación y eliminación; luego inferencia sin red.                                   |
| F09 | Persistencia cifrada     | Perfiles y embeddings protegidos; clave en Keychain; errores de acceso y recuperación sin sobrescribir datos.                                            |
| F10 | Diagnóstico              | Estado del servicio/modelos/entrada, errores accionables y métricas; sin grabación de voz ni secretos en logs.                                           |

La beta base requiere F01–F06, F08–F10. F07 entra como experimental solo si supera el benchmark; si no lo supera, se retrasa y se comunica expresamente que la beta no cumple todavía «solo mi voz». Una beta con esa promesa requiere además F07 aprobado.

Estados comunes: iniciando, permiso pendiente/denegado, sin dispositivo, modelo no instalado, descargando, listo, procesando, silenciado, fallo y recuperación. No simular éxito de persistencia o del mute.

Fuera de alcance: cuentas, sincronización, servidores Cloud, pagos, aislamiento perfecto de personas hablando a la vez y servicio siempre activo. El BFF **local** HTTP/SSE sí está implementado; gRPC solo se incorpora si un adaptador lo requiere.

### Compatibilidad y activación Local

- F11: entrada virtual seleccionable en Teams, Zoom, Google Meet y Slack, con opción explícita de convertirla en predeterminada del sistema y restaurar la anterior. Las apps con entrada física fijada requieren reconfiguración.
- F12: servicio vivo solo con la app abierta; inferencia/captura activadas al abrir la entrada virtual el primer consumidor, reposo al cerrar el último. La detección fiable de consumidores es una puerta de salida del spike; se prueba con varios consumidores y sin contar al productor.
- F13: detección de voz dentro de una sesión activa, sin iniciar/detener el dispositivo por cada silencio ni perder el principio de las palabras. Esto no sustituye a detectar si una aplicación usa el micrófono.

F11–F13 forman parte de la beta Local y requieren evidencia real. Cloud futura será por aplicación, con configuración de sesiones y transporte independiente; no tiene funciones implementadas.

### Instalación y mantenimiento

- F14: instalador Local macOS firmado con UI, servicio, runtimes y pesos seleccionados/verificados; sin herramientas globales de desarrollo. Funciones offline declaradas y comprobadas.
- F15: desinstalación desde Ajustes y acceso de recuperación, con elección de conservar perfiles o eliminar datos, cierre de procesos y limpieza verificable de componentes propios. Preservar dependencias preexistentes/compartidas.

F14–F15 son requisitos de beta externa. Cloud tendrá su propio agente de audio sin IA local; Windows es adaptación futura. Ver [installation.md](installation.md).

## Ampliación confirmada de F03

Una persona podrá guardar varios perfiles de ajustes, usar plantillas predefinidas por la app y crear perfiles
personalizados. Duplicar una plantilla permite personalizar una copia. Sin login; perfil de voz independiente
y opcional. Ver [comportamiento y pendientes](profiles.md) y T007 en el [backlog](backlog.md).
La selección por sí sola no inicia captura. Esta ampliación está especificada, no implementada.
