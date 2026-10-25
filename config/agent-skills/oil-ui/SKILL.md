---
name: oil-ui
description: "Actívala cuando el usuario pida diseñar, rediseñar, mejorar o evaluar visualmente una web, aplicación, pantalla de escritorio o móvil, panel o componente. Úsala para definir una dirección visual, implementar interfaces y verificar su apariencia. No la uses para tareas de lógica, API o cambios visuales puntuales ya especificados."
metadata:
  version: "0.25.0"
  compatibility: "Guía portátil para Codex, Cursor, Antigravity, Hermes y agentes nativos lanzados desde Agent Hub."
---

# Oil UI

Diseña interfaces reconocibles y fáciles de usar. Define una idea visual central y haz que composición, tipografía, color, imágenes e interacción trabajen a favor de ella. La sobriedad consiste en conservar lo que aporta, no en volver todas las interfaces iguales. Evalúa por separado la calidad visual y el flujo de uso.

Respeta primero la marca, las referencias y las decisiones del usuario. Deduce el estilo del producto, su público, el contenido principal y la tarea que la persona necesita completar. Evita aplicar una plantilla estética por defecto.

## Alcance y decisiones

- Revisa solo los archivos y pantallas relacionados con la solicitud. Sigue las instrucciones y convenciones del proyecto.
- Distingue entre una propuesta, un diseño visual y una interfaz funcional. Entrega el tipo de resultado que pidió el usuario; no cambies archivos si solo pidió una evaluación.
- Si el usuario especificó exactamente un ajuste visual, aplícalo directamente. Comprueba el resultado en contexto cuando afecte color, espacio o estilo; los cambios de texto o contenido pueden entregarse sin abrir el navegador.
- Para una interfaz nueva o un rediseño abierto, define el público, la tarea principal, el contenido realista, el dispositivo y el resultado esperado. Explora alternativas internamente y elige la que mejor encaje. Pregunta solo si falta una decisión que cambie materialmente el resultado y no pueda inferirse.
- Si el usuario pide comparar opciones, prepara hasta tres direcciones claramente diferenciadas y deja que elija. Si pidió completar el trabajo o delegó la decisión, selecciona la mejor y continúa sin pausar para pedir preferencia estética.
- Al mejorar un producto existente, conserva su identidad y componentes útiles. Una mejora visual permite corregir decisiones accidentales; una nueva función o flujo debe seguir el lenguaje visual actual.
- Para reproducir una referencia, úsala como criterio visual, confirma el tamaño de pantalla y compara capturas durante la implementación.

## Dirección y construcción

Antes de diseñar, identifica el tipo de producto, qué debe entender o hacer la persona al entrar y qué convenciones visuales de productos comparables son relevantes. Define una dirección breve y una jerarquía clara. Mantén un solo foco principal por pantalla y no llenes la página de tarjetas sin una razón de contenido.

Construye el recorrido y los estados importantes, no solo una pantalla vacía atractiva. Considera estados de carga, error, éxito y ausencia cuando apliquen. Usa textos y datos verosímiles; no inventes métricas, testimonios ni resultados. No añadas notas de implementación a la interfaz.

Elige imágenes y otros recursos por la función que cumplen. Si una imagen debe ser el foco visual, consíguela o créala antes de terminar la composición. Usa servicios alojados, generación de imágenes de pago o cualquier servicio externo solo si el usuario lo solicitó o autorizó. Prioriza recursos locales y herramientas existentes.

En un proyecto existente, modifica los estilos y componentes en su origen. Reutiliza tokens, patrones y dependencias presentes; evita crear sistemas paralelos o incluir refactors que no ayuden a la interfaz pedida. Sigue las reglas de arquitectura del proyecto.

## Verificación

- Revisa la interfaz en el entorno y tamaño de pantalla previstos. Una captura guardada no cuenta como inspección: abre y mira la evidencia.
- Comprueba jerarquía, alineación, contraste, recortes, estados y textos largos. Revisa los tamaños móviles cuando la tarea los incluya.
- Si cambiaste un flujo, recórrelo desde su entrada hasta un resultado visible. Ejecuta las comprobaciones de lint y tipos que indique el proyecto.
- Para cambios pequeños, mira el área modificada y sus elementos vecinos. Para una pantalla nueva o un rediseño, revisa todas las áreas y estados relevantes.
- Haz una pasada final para quitar decoración o explicaciones repetidas sin borrar etiquetas, contexto, estados ni acciones necesarias.
- No inicies agentes auxiliares ni delegues revisiones salvo que el usuario o las reglas del proyecto lo autoricen. Puedes hacer una autoevaluación visual y señalar con honestidad si el entorno impidió verificarla.

En la entrega, resume la dirección elegida y su motivo, los cambios realizados, qué validaste y cualquier limitación relevante. No afirmes que una interfaz se ve bien o que una interacción funciona si no pudiste comprobarla.

## Privacidad y actualización

No compruebes versiones automáticamente. No envíes telemetría ni contenido del proyecto a servicios externos. Usa búsqueda web, servicios externos o herramientas alojadas solo cuando el usuario lo pida o lo autorice expresamente. No solicites ni uses servicios de pago sin autorización.

Las guías especializadas están en `references/`. Carga solo la referencia pertinente a la tarea. La captura del navegador se describe en `references/tools.md`; el trabajo exploratorio y las comparaciones visuales, en `references/style-explorer.md`; la dirección visual, en `references/design-direction.md`; y la accesibilidad visual, en `references/visual-language.md`.
