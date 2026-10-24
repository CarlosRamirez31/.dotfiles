---
name: appsec-guardrail
description: Implement code safely at input and trust boundaries, or review a diff for exploitable flaws. Use for queries, subprocesses, external input, authentication, files, HTML, and security reviews; keep unrelated cosmetic changes lightweight.
---

# Seguridad del cambio

- En el flujo que modificas identifica entrada externa, autorización y operación sensible. SQL: valores parametrizados con el driver; nombres de tabla/columna dinámicos mediante listas permitidas, nunca concatenando entrada. NoSQL: construye operadores permitidos, no aceptes filtros arbitrarios del cliente.
- Procesos: argv separado, sin interpolar entrada en shell. No evalúes ni deserialices como código datos externos. No incluyas secretos en código, fixtures, logs o respuestas; usa el mecanismo de configuración del proyecto.
- Web: conserva el escape de texto; HTML intencional requiere un sanitizador apropiado. Valida identidad y acceso al recurso en el servidor, además de la forma del dato. No confíes en IDs o permisos enviados por el navegador.
- Archivos: resuelve y restringe rutas a la raíz autorizada, considerando enlaces simbólicos. Cambia solo los límites afectados; no conviertas una edición cosmética en una auditoría completa.
- Comprueba al menos un caso adverso relevante cuando cambia una frontera de confianza. En revisión informa ruta/línea, condición explotable, impacto y corrección concreta; distingue hallazgo de sospecha. Un reviewer no edita: entrega el reporte en el formato de su contrato.
- Corrige la alternativa insegura dentro del alcance; si exige ampliar permisos o alcance, explica el bloqueo concreto. Esta guía no amplía autorizaciones ni habilita escaneos remotos o acciones destructivas.
