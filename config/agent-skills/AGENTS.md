# Preferencias de programación

En tareas de código, resuelve lo pedido con el cambio mínimo completo, conserva el trabajo previo y respeta las instrucciones del proyecto. Busca primero con `rg`, lee el contexto necesario y amplía solo por una dependencia real. Evita refactors, paquetes y abstracciones ajenos al encargo. Verifica proporcionalmente y responde breve con resultado y evidencia.

Skills disponibles: `context-efficiency` para seleccionar contexto pertinente y reutilizar evidencia vigente; `surgical-edits` para cambios locales; `anti-overengineering` para decisiones de implementación; `repo-scaffold` para repositorios nuevos; `software-architect` para estructura e integraciones; `appsec-guardrail` para entradas y operaciones sensibles. Puedes combinar skills: arquitectura + repo-scaffold al crear una aplicación; arquitectura + AppSec al diseñar entradas sensibles; edición puntual + simplicidad al añadir una función local. Carga solo las relevantes; no hace falta abrir otro agente para usar una skill. Usa consultas parametrizadas y argv sin interpolación de entrada externa; no expongas secretos. No hagas una auditoría completa por cambiar un color.

Los proyectos nuevos van por defecto en `~/Documents/Programacion/` (en Hermes: `/host-home/Documents/Programacion/`). Un worktree asignado por Agent Hub tiene prioridad como ubicación de trabajo. Las skills no amplían scope, permisos, autorizaciones ni presupuestos. No arranques otros agentes para un cambio sencillo.

La memoria de cada proyecto se guarda fuera de su código, en `~/Documents/Agentes/proyectos/`, compartida por los agentes y conversaciones. Identifica el proyecto por su directorio real del sistema; no requiere Git ni autoriza crear `.git`. Al iniciar una tarea de código, consulta `dotfiles-project-context show --project <directorio>` y lee solo el resumen pertinente. Si no está registrado, `init --project <raíz-del-proyecto>` crea únicamente su referencia externa. No analices todo el proyecto para llenar documentos. Consulta el procedimiento de memoria en `software-architect` al diseñar o cambiar su estructura. No crees AGENTS.md, notas o planes del agente dentro del proyecto ni muevas documentos existentes sin una solicitud explícita. Los worktrees en directorios distintos son proyectos distintos salvo asociación explícita del usuario. En Hermes ejecuta `/host-home/.dotfiles/bin/dotfiles-project-context`; el montaje `/host-home` identifica la misma carpeta del anfitrión. No salgas del scope ni amplíes permisos para escribir memoria: si el sandbox solo permite el worktree, entrega la actualización pendiente en el resultado.


Antes de modificar código es obligatorio consultar la arquitectura externa de ese
proyecto y contrastar el área afectada con el código actual. No basta con que el
archivo exista: lee su contenido y respeta sus límites y decisiones pendientes.
Si falta, primero analiza lo necesario y documéntalo con `software-architect`;
si está incompleta para la tarea, explica qué puedes hacer, qué queda bloqueado y
qué decisión concreta hace falta. Guarda borradores con `--status draft` y usa
`--status defined` cuando la estructura, responsabilidades y alcance de la tarea
estén definidos. No inventes una arquitectura para desbloquear un cambio.
Para proyectos nuevos combina `software-architect`, `repo-scaffold` y
`anti-overengineering`: propone la estructura mínima apropiada al stack; no crees
capas por rutina. Ningún agente implementa sobre arquitectura ausente o en borrador.
Este requisito también aplica al abrir un agente directamente, no solo por Agent Hub.
