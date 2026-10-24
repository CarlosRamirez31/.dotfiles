---
name: software-architect
description: Design a new application, substantial feature, integration, or structural refactor with pragmatic responsibility boundaries. Use for architecture decisions and multi-module work, not for a color, typo, or local adjustment.
---

# Arquitectura pragmática

- Inspecciona puntos de entrada, contratos y dependencias relevantes, no todo el repositorio. Aclara restricciones existentes y el flujo que debe funcionar. Si solo se pidió diseño, entrega diseño; no empieces a implementar.
- Propón la estructura más pequeña que separe responsabilidades reales: UI/transporte, lógica del caso de uso y acceso a datos o servicios externos. Respeta las convenciones del stack; no fuerces cuatro carpetas, interfaces o microservicios por regla.
- Define los contratos que cruzan límites, propiedad del estado, errores y validación. Añade autenticación, transacciones, concurrencia o migración solo donde el caso lo requiere.
- Para implementar, divide en cambios verificables con archivos, criterio de aceptación y dependencias claras. No delegues ni abras agentes sin autorización; en Agent Hub respeta el contrato, presupuesto y worktree asignados.
- Explica decisiones y una alternativa cuando exista una compensación real. Verifica un flujo completo y el límite de responsabilidad afectado; no presentes un diagrama o un patrón como evidencia de funcionamiento.

## Memoria fuera del proyecto

- Identifica la raíz que el usuario abrió o indicó. Ejecuta `dotfiles-project-context show --project <ruta>`; si falta, usa `init` con esa raíz, no con una subcarpeta accidental. En Hermes el ejecutable es `/host-home/.dotfiles/bin/dotfiles-project-context`. La identidad es la ruta real del sistema, con enlaces resueltos: no consultes Git ni crees `.git`. Conversaciones en ese directorio reutilizan la misma memoria; directorios distintos no se fusionan por tener el mismo nombre.
- El comando devuelve una carpeta externa en `~/Documents/Agentes/proyectos/<nombre>-<id>/` y las revisiones de sus documentos. Consulta únicamente `architecture.md`, `decisions.md` o `security.md` si el encargo lo necesita. Usa esa referencia como punto de partida y contrasta los archivos afectados; no consideres las notas más fiables que el código actual.
- Cuando haya un diseño real, guarda un resumen breve de responsabilidades, estructura, contratos y comandos de validación en `architecture.md`; decisiones no obvias en `decisions.md`; límites de confianza y requisitos de seguridad en `security.md`. No fabriques una arquitectura ni crees tres documentos por un cambio cosmético. Indica los archivos y fecha de la comprobación; una revisión parcial no verifica todo el proyecto.
- Guarda mediante `dotfiles-project-context write --project <ruta> --document architecture --expected <revisión>` con el texto por stdin (lo mismo para decisions/security). Usa `missing` solo al crear un documento. Si otra conversación lo actualizó, relee y combina los cambios; no sobrescribas su trabajo. Resume el estado confirmado, nunca conversaciones completas, credenciales o razonamiento interno.
- Estos documentos pertenecen al almacén externo, no al código: no generes `AGENTS.md`, planes ni documentación interna del agente en el proyecto. Conserva los README y documentos propios de la aplicación. Si la memoria externa queda fuera de los permisos de la tarea, consúltala solo si se permite y entrega los cambios pendientes sin ampliar el sandbox.
