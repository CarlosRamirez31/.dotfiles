# UI/UX Local — propuesta de estándares

Especificación preparada con el flujo de Product Design y las referencias aportadas por el usuario.
Estado: propuesta visual, sin implementación de estilos ni aprobación visual todavía. Ver [tickets](backlog.md).

## Referencias y alcance

De Krisp se toma el panel compacto anclado a la barra de menús y la selección clara del micrófono.
De NVIDIA Broadcast se toma la separación entre entrada, efectos y prueba de audio. No se copian marcas,
logotipos ni su paleta. No se incorporan cuenta, vídeo, procesamiento de altavoces, eco ni Studio Voice.
La prioridad es usar la app rápidamente durante una llamada, con controles cuyo estado confirme el servicio.

## Personas y perfiles

Reuniones cotidianas, trabajo en lugares ruidosos y creación de contenido son escenarios de diseño, no roles
con permisos distintos. Una persona puede usar todos ellos. Ver [perfiles](profiles.md): plantillas propias,
varios perfiles guardados y personalizados, sin login. La identidad de voz es independiente de los ajustes.

## Superficies

- **Panel de barra de menús:** ancho propuesto 360 px, mínimo 320; altura limitada a la pantalla con scroll.
  Orden: estado textual, perfil seleccionado, entrada, reducción de ruido, voz personal experimental,
  acción de sesión y mute cuando exista. Pie: Ajustes y Salir. Nivel solo si hay medición real.
- **Ajustes:** ventana secundaria propuesta de 800 × 600, adaptable; secciones Perfiles, Audio y voz,
  Modelos, Diagnóstico y Mantenimiento. No convertir cada módulo técnico en una sección visible.
- **Primera apertura:** explicar procesamiento local, seleccionar entrada, pedir permiso cuando se use,
  presentar modelos faltantes y descarga explícita; ayudar a elegir la entrada virtual en la app de llamadas.
  Registro de voz opcional, con límites experimentales. Terminar no inicia captura automáticamente.
- **Prueba de audio:** acción voluntaria secundaria; comparar original/filtrado e indicar duración y eliminación
  de la muestra. No reproducir hacia la entrada virtual produciendo realimentación.

Escape y clic fuera ocultan el panel; devolver foco al origen cuando corresponda. Ocultar no equivale a salir.
Salir termina servicio y workers. Probar bordes, varios monitores, escalado y reapertura desde teclado.

## Estados y confirmaciones

| Estado                       | Mensaje / acción                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------- |
| Iniciando                    | Preparando servicio; controles dependientes en espera                             |
| Permiso pendiente / denegado | Explicar acceso al micrófono y ofrecer abrir ajustes del sistema                  |
| Sin dispositivo              | Seleccionar entrada disponible; no cambiar silenciosamente                        |
| Modelo no instalado          | Mostrar capacidad, tamaño y acción Descargar                                      |
| Descargando                  | Progreso real o indeterminado; Cancelar; no mostrar Listo antes de verificar hash |
| Listo                        | Servicio disponible; no implica que alguien escuche ni que capture                |
| Procesando                   | Sesión confirmada; entrada y salida visibles                                      |
| Silenciado                   | Solo tras confirmación del mute del flujo controlado                              |
| Cancelación solicitada       | Esperar cierre; no mostrar Detenido prematuramente                                |
| Fallo                        | Causa accionable y reintento; conservar datos y configuración                     |
| Reconectando / recuperación  | Recuperar estado por operación; no reiniciar captura                              |

HTTP 202 significa trabajo aceptado, no completado; correlacionar SSE por operación y recuperar estado al
reconectar. Distinguir servicio conectado, sesión activa y consumidor detectado. No mostrar nombres de apps
ni Uso del micrófono detectado sin evidencia real. La implementación actual permite iniciar/cancelar;
mute, bypass, selector de perfiles y gestor de modelos requieren sus tickets antes de ofrecerlos funcionalmente.

## Sistema visual propuesto

Tema del sistema por defecto; preferencias claro/oscuro. Superficies opacas para mantener contraste predecible.
Azul para acción/foco; verde para éxito confirmado; ámbar para advertencia; rojo para error/destrucción.
Siempre acompañar estado con texto o icono etiquetado, nunca solo color.

| Token              | Claro   | Oscuro  |
| ------------------ | ------- | ------- |
| Fondo              | #F6F8FA | #0F1720 |
| Superficie         | #FFFFFF | #18232F |
| Superficie elevada | #EEF2F6 | #223140 |
| Texto              | #16202B | #F2F6FA |
| Texto secundario   | #4B5D6B | #AEBCCB |
| Acción / foco      | #155AC5 | #82B4FF |
| Éxito              | #146C43 | #6BD6A3 |
| Advertencia        | #805500 | #F4C66A |
| Error              | #B42318 | #FFAAA3 |

Fuente del sistema, cuerpo 13–15 px, título 20 px; interlineado al menos 1.4. Espaciado 4/8/12/16/24/32 px,
radios 8/12/16 px. Controles compactos con área de interacción mínima interna de 36 px, primaria 40 px.
Tokens propuestos en [design-tokens.json](design-tokens.json); aún no están conectados a React.

Componentes: selector con etiqueta persistente, switch con estado y explicación, botón primario por contexto,
banner de error recuperable, progreso, tarjeta de perfil, confirmación destructiva y medidor con unidad.
No mezclar silenciar con detener sesión. Deshabilitados explican por qué; error conserva valores editados.

## Accesibilidad y privacidad

Objetivo de texto normal ≥4.5:1 y texto grande ≥3:1, según
[WCAG contraste](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
El mínimo general WCAG de objetivo es 24 × 24 CSS px con excepciones; nuestro objetivo interno de 36 px
es más amplio: [tamaño de objetivos](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
Foco visible de 2 px y separación de 2 px; teclado completo, etiquetas VoiceOver, orden de foco lógico,
mensajes de estado sin anunciar cada bloque de audio. Respetar reducción de movimiento; transición 120 ms
solo decorativa, nunca necesaria para entender estado. No usar opacidad para texto informativo.

[Contraste calculado](design-contrast.md) comprueba colores, no certifica accesibilidad de una UI todavía inexistente.
Probar VoiceOver, zoom/texto largo, temas y foco en T023. Separadores decorativos no sustituyen bordes de controles.

Antes de registrar voz: explicar muestra de 10 segundos, procesamiento local en RAM, embedding cifrado,
cancelación y límites ante voces superpuestas. No afirmar borrado seguro de RAM sin verificarlo.
Eliminar voz debe explicar qué perfiles pierden la referencia. Sin audio, embeddings ni secretos en logs.

## Entrega y aprobación

T005 entrega especificación y tokens; revisión visual pendiente. T006 implementará panel; T007 perfiles;
T012 voz y consentimiento; T023 QA. No se considera funcional una maqueta ni se marca beta por compilar.
