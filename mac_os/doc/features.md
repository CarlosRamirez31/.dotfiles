# Funcionalidades de la beta Local

Todos los elementos están pendientes; documentar no equivale a implementarlos.

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

Fuera de alcance: cuentas, sincronización, BFF, servidores, pagos, aislamiento perfecto de personas hablando a la vez y servicio siempre activo.

### Compatibilidad y activación Local

- F11: entrada virtual seleccionable en Teams, Zoom, Google Meet y Slack, con opción explícita de convertirla en predeterminada del sistema y restaurar la anterior. Las apps con entrada física fijada requieren reconfiguración.
- F12: servicio vivo solo con la app abierta; inferencia/captura activadas al abrir la entrada virtual el primer consumidor, reposo al cerrar el último. La detección fiable de consumidores es una puerta de salida del spike; se prueba con varios consumidores y sin contar al productor.
- F13: detección de voz dentro de una sesión activa, sin iniciar/detener el dispositivo por cada silencio ni perder el principio de las palabras. Esto no sustituye a detectar si una aplicación usa el micrófono.

F11–F13 forman parte de la beta Local y requieren evidencia real. Cloud futura será por aplicación, con configuración de sesiones y transporte independiente; no tiene funciones implementadas.

### Instalación y mantenimiento

- F14: instalador Local macOS firmado con UI, servicio, runtimes y pesos seleccionados/verificados; sin herramientas globales de desarrollo. Funciones offline declaradas y comprobadas.
- F15: desinstalación desde Ajustes y acceso de recuperación, con elección de conservar perfiles o eliminar datos, cierre de procesos y limpieza verificable de componentes propios. Preservar dependencias preexistentes/compartidas.

F14–F15 son requisitos de beta externa. Cloud tendrá su propio agente de audio sin IA local; Windows es adaptación futura. Ver [installation.md](installation.md).
