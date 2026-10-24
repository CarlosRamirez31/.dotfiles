---
name: surgical-edits
description: Make a focused code or UI change with bounded context and a minimal complete diff. Use for local fixes, small features, spacing, colors, labels, and targeted bug fixes.
---

# Cambios puntuales

- Identifica el resultado pedido y el archivo responsable con `rg` y lecturas por rango. Amplía al contexto de sus llamadas solo si hace falta; no cargues el repositorio ni historiales completos para una edición local.
- Conserva los cambios previos del usuario. Cambia el bloque responsable y sus dependencias reales, sin reformatear archivos ajenos ni añadir mejoras no pedidas. No impongas un número de líneas: el diff debe ser mínimo **y completo**.
- Para un ajuste visual usa los tokens, componentes y márgenes existentes. Verifica el resultado visible y que no recorte iconos o texto. No reinicies el escritorio para aplicar un menú.
- Ejecuta la comprobación más pequeña que detecte un fallo real. Un color o texto no requiere inventar tests ni lanzar toda la suite. Para cambios de comportamiento prueba el caso afectado; amplía solo ante fallos o riesgo relacionado.
- Al terminar, informa resultado y validación en pocas líneas. No prometas cifras de ahorro ni rapidez que no mediste. Si el alcance crece, explica la dependencia concreta antes de tocar más áreas.

- Si hay memoria externa del directorio, consulta solo la nota pertinente como referencia; contrasta el bloque afectado. Un color o etiqueta no obliga a volver a analizar la arquitectura ni a actualizar sus documentos. No generes notas del agente dentro del proyecto.
