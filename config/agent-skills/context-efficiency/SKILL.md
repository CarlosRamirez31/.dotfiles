---
name: context-efficiency
description: Reduce repeated context and unnecessary reading during programming tasks, project handoffs, and multi-step investigations. Use to select relevant skills and reuse verified project knowledge while preserving architecture and safety requirements.
---

# Contexto eficiente

## Inicio de sesión

Prioriza exactitud y trabajo completo. Carga solo skills pertinentes. Busca y lee lo necesario; reutiliza evidencia vigente. Termina la investigación cuando lo pedido tenga respaldo suficiente; amplía ante vacíos o contradicciones. En código, respeta arquitectura, permisos y pruebas proporcionales. No repitas comprobaciones sin cambios o fallos que lo justifiquen.

## Guía bajo demanda

- Prioriza exactitud, trabajo completo y el detalle solicitado. Amplía lectura, análisis y pruebas cuando hagan falta; no impongas límites de razonamiento ni respuestas cortas por ahorrar. En preguntas cotidianas aplica solo los criterios pertinentes, sin exigir arquitectura ni procedimientos de programación.
- Selecciona skills por la tarea y sus límites reales; carga su contenido al necesitarlo. Conserva las solicitadas explícitamente. Si aparece una dependencia nueva, añade la skill pertinente antes de trabajar en ella; no cargues todas por rutina.
- Consulta la arquitectura externa del directorio y contrasta el área afectada con el código actual. Reutiliza sus referencias; no vuelvas a inventariar el proyecto. Una arquitectura ausente o en borrador sigue bloqueando la implementación.
- Busca rutas y símbolos con `rg`; lee rangos que expliquen el comportamiento y amplía por llamadas, contratos o fallos concretos. Acota salidas grandes y recupera el fragmento omitido si es necesario; no tomes una salida truncada como evidencia completa.
- Reutiliza hallazgos y comprobaciones solo si siguen vigentes: misma revisión o archivos sin cambios y mismo entorno relevante. Ante cambios concurrentes, errores o evidencia contradictoria, vuelve a verificar el área afectada.
- Al transferir contexto conserva objetivo, directorio real, arquitectura/revisión, archivos afectados, decisiones, validación y pendientes. Resume resultados observables; no copies conversaciones completas, secretos ni razonamiento interno.
- Ajusta la verificación al riesgo y comunica resultado, evidencia y límites brevemente. El ahorro no reduce controles de arquitectura, seguridad, permisos ni pruebas necesarias. No prometas porcentajes de tokens sin medirlos.
