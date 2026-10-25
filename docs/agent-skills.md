# Skills de programación compartidas

Las skills locales se mantienen en `config/agent-skills/`; no descargan prompts
remotos ni cambian modelos. Seis cubren programación y `oil-ui` se carga para
diseño o revisión visual de interfaces.

| Skill | Cuándo se usa |
| --- | --- |
| `context-efficiency` | Lectura acotada, selección de skills y reutilización de evidencia vigente |
| `oil-ui` | Diseño, rediseño, mejora y verificación visual de interfaces |
| `surgical-edits` | Corrección local, texto, colores, espaciado, bug puntual |
| `anti-overengineering` | Implementación sin abstracciones o paquetes innecesarios |
| `repo-scaffold` | Repositorio nuevo en `~/Documents/Programacion/`, salvo ubicación explícita |
| `software-architect` | Diseño de aplicaciones, integraciones y cambios estructurales |
| `appsec-guardrail` | Entradas externas, queries, procesos, autorización, archivos y revisión AppSec |

No hay un límite artificial de líneas ni se ejecutan auditorías por cambiar un color.
La verificación debe corresponder al comportamiento afectado. Las instrucciones no
sustituyen los permisos, sandbox, scope o presupuesto del contrato.

## Agentes individuales

- **Codex:** `~/.agents/skills/<nombre>/SKILL.md`, con preferencias breves en
  `~/.codex/AGENTS.md` (respeta `CODEX_HOME`). Puede invocarse con `$surgical-edits`,
  por ejemplo; también se permite selección automática.
- **Antigravity CLI:** `~/.gemini/config/skills/<nombre>/SKILL.md` y preferencias
  en `~/.gemini/config/AGENTS.md`, usando su descubrimiento global documentado.
- **Cursor:** `~/.cursor/skills/<nombre>/SKILL.md`; Codex también usa el directorio
  compartido `~/.agents/skills/`. Agent Hub lanza los CLIs nativos y estos usan
  sus skills locales.
- **Hermes:** skills en `/opt/hermes/.hermes/skills/programming/` dentro de
  `dev-podman`. Se añadió un bloque acotado de preferencias de código a su `SOUL.md`,
  conservando su identidad y otras instrucciones. `hermes skills list` las muestra
  como locales y habilitadas.

Las skills nativas se descubren por nombre/descripción; se carga el cuerpo al
necesitarlo. De `context-efficiency` solo se incorpora un resumen breve al inicio;
la guía completa queda bajo demanda. Las sesiones que ya arrancaron pueden conservar instrucciones antiguas:
abre una sesión nueva o retoma la existente después de cerrar su CLI para refrescarlas.
Esto no evita que Antigravity tenga que esperar a que se restablezca su cuota.

## Agent Hub y Coucou

Las seis skills de programación se registran en el scope `global`. Oil UI se
distribuye a los agentes nativos, pero no se registra como skill global de Hub:
Hub incluye las skills globales personalizadas en cada tarea y eso añadiría una
guía de diseño extensa incluso a trabajos sin interfaz. Hub carga `context-efficiency` solo si
el contrato o perfil la solicita explícitamente; añade
`software-architect` para complejidad medium/complex/critical o dominio architecture,
y simplicidad y AppSec para escritura, edición puntual
para cambios pequeños y AppSec para red o dominio security. `repo-scaffold` llega
cuando lo solicita el contrato (el planificador lo hace para proyectos nuevos).
Las skills explícitas del contrato/perfil siempre se conservan, con los controles
de privacidad existentes. Las globales personalizadas siguen incluyéndose siempre.
Los cuerpos seleccionados siguen sujetos al presupuesto del context pack. La lectura
de arquitectura definida continúa siendo obligatoria para cualquier edición, también
cuando no se inyecta el cuerpo completo de software-architect.

Perfiles nuevos, heredando comandos, contenedores y configuración de modelo:

- `antigravity-architect`: worker de arquitectura, con `software-architect`.
- `hermes-appsec`: reviewer de seguridad, con `appsec-guardrail`, filesystem de
  lectura, sin red, instalación de dependencias, commits ni push.

No se alteran los perfiles originales ni las policies, aprobaciones o asignaciones
fijas existentes. El registro no ejecuta agentes ni consume cuota. Desde Coucou:

```text
/tarea architect Diseñar la integración de pedidos
/tarea antigravity-architect Diseñar el módulo de facturación
```

Ambos preparan un plan de Hub con asignación fija al arquitecto. La ejecución
conserva los controles del Hub sobre repositorio, permisos y checks. El perfil
`hermes-appsec` se selecciona como reviewer de seguridad en la configuración del
run; no se ofrece como worker de implementación.

## Reinstalar o actualizar

```sh
./install.sh agent-skills
# Además de los enlaces y reglas nativas:
dotfiles-agent-skills --hub --hermes dev-podman
```

La instalación es repetible. Conserva reglas personales fuera de sus marcadores;
no sobrescribe skills nativas ajenas con el mismo nombre. Copias de reglas y
perfiles previos en `~/.local/state/dotfiles/agent-skills/`; Hermes guarda sus
copias dentro de `/opt/hermes/.hermes/backups/`. Los perfiles especializados que
ya existan se conservan; las seis skills de programación globales del Hub se actualizan desde
su fuente al repetir `--hub`.

Oil UI conserva sus referencias y recursos locales. No consulta versiones ni
envía telemetría; búsqueda o servicios externos requieren autorización expresa.

Validación: frontmatter de las skills, descubrimiento real de Hermes,
instalación repetida, preservación de reglas/skills ajenas, alias de Coucou y
context pack real en un worktree temporal sin modelos.

## Memoria externa por directorio, sin Git

Los documentos internos del agente no van en el árbol de código. El almacén es
`~/Documents/Agentes/proyectos/<nombre>-<id>/`, compartido por Codex, Antigravity y
Hermes. El ID se calcula a partir de la ruta real del directorio, no de `.git`,
la conversación, el nombre del proyecto ni un remoto. No crea repositorios Git.

```text
Documents/Programacion/ppe/                  # código
Documents/Agentes/proyectos/ppe-<id>/         # memoria del agente
    project.json                            # asociación al directorio
    architecture.md                         # cuando exista un diseño real
    decisions.md                            # decisiones relevantes, si las hay
    security.md                             # límites de confianza, si aplica
```

Cinco conversaciones en la misma carpeta obtienen la misma referencia. Se
resuelven enlaces simbólicos; una conversación en una subcarpeta reutiliza la
raíz ya registrada más cercana. En el primer registro se debe indicar la raíz
que el usuario abrió, no inferirla a partir de Git ni registrar `src/` por error.
Dos carpetas diferentes llamadas `ppe` tienen IDs distintos. Worktrees en
rutas distintas también son distintos; mover un proyecto requiere reasociación
explícita, no se fusionan memorias por semejanza.

```sh
dotfiles-project-context init --project "$HOME/Documents/Programacion/ppe"
dotfiles-project-context show --project "$HOME/Documents/Programacion/ppe/src"
# Después de consultar la revisión actual; el texto entra por stdin:
dotfiles-project-context write --project "$HOME/Documents/Programacion/ppe" \
    --document architecture --expected missing < /ruta/al/resumen-validado.md
```

`init` solo crea metadatos externos. No inventa arquitectura, no lee el código
del proyecto ni genera documentos vacíos. Los resúmenes se guardan tras diseñar
o comprobar el comportamiento; se consultan por relevancia y se contrastan con
los archivos afectados. Un cambio cosmético no obliga a releer ni regenerar toda
la documentación. No se mueven README ni otros archivos existentes del proyecto.

Cada escritura es atómica y exige la revisión SHA-256 devuelta por `show` (o
`missing` al crear). Si otra conversación guardó antes, la actualización se
rechaza para releer y combinar; nunca se resuelve sobrescribiendo ciegamente.
Eso evita perder cambios, pero no bloquea ni coordina ediciones simultáneas al
código del proyecto: esa responsabilidad sigue en los contratos y agentes.

Hermes utiliza `/host-home/.dotfiles/bin/dotfiles-project-context`; su montaje
`/host-home/Documents/...` corresponde al directorio del anfitrión y comparte
el mismo almacén. Las skills contienen ese procedimiento. No hay inyección
automática de toda la arquitectura en cada mensaje: se consulta cuando aporta
contexto. Un sandbox que solo autorice escribir el worktree no obtiene permiso
para modificar el almacén; el agente entrega la actualización pendiente en su
resultado para guardarla desde un contexto autorizado.

## Cursor CLI

El mismo instalador incluye `~/.cursor/skills/` con las cinco skills compartidas.
Un hook `sessionStart` ejecuta `dotfiles-cursor-context` para incorporar las
preferencias de programación y la consulta de memoria externa por directorio.
Conserva los hooks personales y los observadores de Agent Hub; no escribe reglas
ni notas dentro de los proyectos. Las skills se descubren también al abrir Cursor
directamente. [Directorios oficiales de skills](https://cursor.com/docs/skills).

La biblioteca y los perfiles worker/reviewer se implementan en el repositorio
independiente de Agent Hub. Allí, `agent-hub work init --json` agrega los perfiles
nuevos conservando los anteriores. El cierre tras tres minutos confirmados sin
tarea se configura con `agent-hub idle configure --minutes 3 --install-hooks`;
no necesita reiniciar Awesome ni refrescar la barra. Cursor mantiene sus permisos
nativos y Privacy Mode se configura en la cuenta del proveedor.

## Arquitectura obligatoria antes de escribir código

Los cuatro agentes reciben la misma regla: leer el documento externo, contrastar el
área afectada y resolver sus decisiones pendientes antes de implementar. El estado
`draft` permite análisis, no implementación; `defined` indica un diseño definido
para el alcance descrito, no una auditoría universal de toda la aplicación.

```sh
dotfiles-project-context init --project /ruta/al/proyecto
dotfiles-project-context show --project /ruta/al/proyecto
dotfiles-project-context write --project /ruta/al/proyecto --document architecture --expected missing --status draft --content-file /tmp/arquitectura.md
```

Para actualizar usa la revisión actual de `show`, conservando las aportaciones de
otras conversaciones. Cuando el diseño esté resuelto, guarda con `--status defined`.
No se crea Git ni documentación del agente dentro del código.

El instalador conserva y respalda hooks existentes y agrega un control PreToolUse
para Codex, Cursor y Antigravity; Hermes carga el plugin `dotfiles-architecture`.
La primera escritura recibe el documento; una revisión nueva exige consultarlo de
nuevo. La lectura y la preparación de la memoria siguen disponibles. El control se
complementa con el sandbox y los permisos nativos. Los clientes ya abiertos cargan
los hooks al iniciar una nueva sesión; no es necesario reiniciar el escritorio.

En Coucou, `/tarea auto ...` usa el contrato público de Agent Hub para preparar la
arquitectura y ejecutar cuando el diseño esté definido. `/definir RUN-001 ...`
continúa las decisiones pendientes sin perder la referencia al directorio.

## Context-efficiency al iniciar sesión

`dotfiles-agent-skills` instala la carga automática sin añadir instrucciones de
uso obligatorio a AGENTS.md. `dotfiles-session-context` lee únicamente la skill
local y extrae únicamente `## Inicio de sesión` (máximo 900 caracteres), sin
inyectar su guía completa. Emite el contrato nativo: SessionStart/additionalContext para Codex,
sessionStart/additional_context para Cursor (conservando sus preferencias previas),
y SessionStart/injectSteps para Antigravity. Codex también vuelve a recibirla al
reanudar o compactar; no hay un hook por mensaje ni un daemon adicional.

Hermes habilita el plugin independiente `dotfiles-context-efficiency`, cuya sección
nativa de sistema incorpora ese mismo resumen al construir el contexto de cada sesión.
No usa pre_llm_call ni repite el contenido por turno. Las sesiones antiguas que
restauran un prompt guardado pueden conservar su versión anterior: abre una sesión
nueva para comprobar la configuración actual. Hub conserva la guía completa bajo demanda.

La carga no prueba obediencia perfecta ni ahorro de tokens. La skill prioriza
exactitud, trabajo completo, verificaciones necesarias y el detalle pedido; para
preguntas cotidianas no exige procedimientos de programación. Si falta el archivo
o supera el límite, el helper informa el error en stderr; no declara una carga
exitosa ni bloquea deliberadamente la sesión. Los hooks anteriores se conservan y
respaldan, y repetir la instalación no duplica los handlers administrados.

Contratos consultados: [Codex](https://learn.chatgpt.com/docs/hooks),
[Cursor](https://cursor.com/docs/hooks), documentación incorporada de Antigravity
(`agy-customizations/docs/hooks.md`) y API instalada de Hermes
(`PluginContext.register_system_prompt_section`).
