# Sprints y preparación de beta

Estimación inicial: **8 semanas para una beta Local de reducción de ruido** y **10–12 semanas para incluir detección personal experimental**, con una persona dedicada y acceso a equipos/dispositivos de prueba. No es una fecha comprometida ni trabajo programado automáticamente. Comienza cuando se autorice implementar; no cuenta desde la creación de estos archivos.

| Sprint | Duración      | Entrega y condición de salida                                                                                                                                                                                           |
| ------ | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S01    | Semanas 1–2   | Spike audio/driver/IA y SQLCipher; benchmark M2, detección de consumidores del driver, licencias, puertos, protocolo y decisiones de runtime. Continuar solo con ruta viable de entrada/salida virtual.                 |
| S02    | Semanas 3–4   | Separación UI/servicio, supervisor, Commons, DI, bus interno, perfiles sin login y repositorios cifrados; cierre y caída del padre sin procesos huérfanos.                                                              |
| S03    | Semanas 5–6   | Pipeline, RNNoise u otro motor elegido, mute controlado, cambios de dispositivo, gestor de modelos y saga de activación; pruebas de llamadas reales en Teams, Zoom, Google Meet y Slack, con activación por consumidor. |
| S04    | Semanas 7–8   | Panel/barra/atajos, errores, instalación, estabilidad, métricas, firma/notarización y QA; candidata beta de ruido.                                                                                                      |
| S05    | Semanas 9–10  | Registro y detección personal, umbrales, benchmark de voces y latencia; decidir incluir experimental o retrasarlo.                                                                                                      |
| S06    | Semanas 11–12 | Correcciones de detección personal, regresión, distribución y prueba con usuarios; candidata beta con voz personal.                                                                                                     |

Ejemplo orientativo: si se comienza el 26 de octubre de 2026, la revisión de beta base sería la semana del 21 de diciembre de 2026, y la revisión con voz personal entre el 4 y el 18 de enero de 2027. Festivos, licencias, firma y resultados de los spikes pueden mover las fechas. No asumir disponibilidad continua durante esas semanas.

## Puertas de salida

- CI verde para las arquitecturas anunciadas; sin fallos críticos conocidos ni dependencias con vulnerabilidades altas/críticas sin resolver.
- Pruebas de hardware, permisos, reinicio, suspensión y llamadas completas con evidencia.
- Servicio no arranca sin app; al salir no queda activo ni capturando.
- Perfiles persistidos, separación de datos y cifrado/recovery probados.
- Modelos y driver con condiciones de distribución resueltas; instalación y eliminación verificadas.
- Sin login, sin envío de audio a red, sin logs de voz; interfaz declara limitaciones reales.
- Firma/notarización e instalación en otro Mac verificadas para beta externa. Un binario CI sin firma no cumple esa puerta.

Cloud no tiene sprint ni fecha en este plan; requerirá planificación propia cuando Local sea estable. El backlog se actualiza con evidencia por entrega, no se marca completado por existir un documento o pasar compilación.

El alcance de S04 incluye F14–F15: instalador completo, inventario, desinstalación desde la app y pruebas de limpieza. La estimación de 8 semanas es provisional: S01 debe estimar también empaquetado de runtimes, driver y auxiliar privilegiado; si no caben en S04 se amplía el calendario antes de comprometer la beta. No se publica beta externa omitiendo el desinstalador.

S01 valida PCM, buffers, calidad/latencia de ambas IA y driver. El control HTTP/SSE y la primera integración de desarrollo ya forman parte de esta entrega, pero eso no completa el sprint ni acredita hardware. S02 consolida perfiles, recuperación y UX. gRPC queda limitado a adaptadores que lo requieran. El usuario amplió el alcance inmediato a ruido y voz personal; las fechas siguen provisionales hasta medir esta integración y empaquetado.
