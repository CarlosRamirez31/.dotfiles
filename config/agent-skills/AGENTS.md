# Preferencias de programación

En tareas de código, resuelve lo pedido con el cambio mínimo completo, conserva el trabajo previo y respeta las instrucciones del proyecto. Busca primero con `rg`, lee el contexto necesario y amplía solo por una dependencia real. Evita refactors, paquetes y abstracciones ajenos al encargo. Verifica proporcionalmente y responde breve con resultado y evidencia.

Skills disponibles: `context-efficiency` para seleccionar contexto pertinente y reutilizar evidencia vigente; `surgical-edits` para cambios locales; `anti-overengineering` para decisiones de implementación; `repo-scaffold` para repositorios nuevos; `software-architect` para estructura e integraciones; `appsec-guardrail` para entradas y operaciones sensibles. Puedes combinar skills: arquitectura + repo-scaffold al crear una aplicación; arquitectura + AppSec al diseñar entradas sensibles; edición puntual + simplicidad al añadir una función local. Carga solo las relevantes; no hace falta abrir otro agente para usar una skill. Usa consultas parametrizadas y argv sin interpolación de entrada externa; no expongas secretos. No hagas una auditoría completa por cambiar un color.

Los proyectos nuevos van por defecto en `~/Documents/Programacion/`. Un worktree asignado por Agent Hub tiene prioridad como ubicación de trabajo. Las skills no amplían scope, permisos, autorizaciones ni presupuestos. No arranques otros agentes para un cambio sencillo.

La memoria de cada proyecto se guarda fuera de su código, en `~/Documents/Agentes/proyectos/`, compartida por los agentes y conversaciones. Identifica el proyecto por su directorio real del sistema; no requiere Git ni autoriza crear `.git`. Al iniciar una tarea de código, consulta `dotfiles-project-context show --project <directorio>` y lee solo el resumen pertinente. Si no está registrado y el almacén está autorizado y es escribible, `init --project <raíz-del-proyecto>` crea únicamente su referencia externa; su ausencia no impide explorar. No analices todo el proyecto para llenar documentos. Consulta el procedimiento de memoria en `software-architect` al diseñar o cambiar su estructura. No crees AGENTS.md, notas o planes del agente dentro del proyecto ni muevas documentos existentes sin una solicitud explícita. Los worktrees en directorios distintos son proyectos distintos salvo asociación explícita del usuario. No salgas del scope ni amplíes permisos para escribir memoria: si el sandbox solo permite el worktree, entrega la actualización pendiente en el resultado.


La arquitectura debe ser proporcional a la tarea. Permite primero leer, buscar,
consultar repositorios, comprobar herramientas y dependencias, estudiar upstream,
obtener baseline de compilación/tests y preparar documentación o borradores, sin
exigir arquitectura registrada. Clonar código autorizado en un destino autorizado
es adquisición/preparación que escribe archivos; conserva sus permisos nativos.

La arquitectura es orientativa, no una condición para ejecutar la tarea. Consulta
el área pertinente y respeta la arquitectura upstream, sin rediseñar ni documentar
todo para una corrección puntual. Si falta arquitectura, está en draft, no cubre
la tarea o quedan decisiones pendientes, muestra un aviso breve:
«Falta definir o actualizar la arquitectura de esta parte. Puedes continuar con
la tarea o definir la arquitectura primero».
Ofrece ambas opciones sin bloquear herramientas ni exigir confirmación por rutina.
Si el usuario ya pidió implementar, continúa con el cambio mínimo razonable e
indica los supuestos necesarios; si prefiere definir la arquitectura primero,
hazlo. Pregunta solo por información imprescindible para cumplir la tarea que no
puedas inferir razonablemente, no por el estado del documento.

En proyectos nuevos explora y propone una estructura mínima apropiada al stack,
sin capas ni documentos por rutina. Un documento defined no demuestra cobertura;
un borrador draft y sus decisiones pendientes son informativos, no bloqueantes.
No fabriques arquitectura ni marques decisiones como resueltas para silenciar avisos.

Registro, persistencia y recibos no son decisiones de diseño. Si la memoria externa
no es accesible o escribible, o no pueden guardarse recibos, informa el límite y
conserva la actualización pendiente fuera del código en una ruta autorizada (por
ejemplo /tmp si está permitido), indicando su ubicación. Si ninguna ruta externa
es escribible, entrega el contenido pendiente en el resultado. La falta de persistencia tampoco impide continuar; no amplíes permisos ni crees memoria dentro
del código. Usa draft para decisiones pendientes y defined para el alcance resuelto.

El hook de arquitectura solo aporta contexto al iniciar sesión; no clasifica
comandos, acredita lectura ni aprueba herramientas. Se mantienen las obligaciones
anteriores y los controles nativos sobre secretos y credenciales, publicación y
push, operaciones destructivas, rutas autorizadas, dinero y servicios externos.
