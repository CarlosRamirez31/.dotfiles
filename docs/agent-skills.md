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
- **Hermes:** queda reservado al trabajo académico, con sus skills e identidad
  propias. Este instalador ya no distribuye programación a Hermes. Para retirar
  una instalación anterior, véase la limpieza selectiva más abajo.

Las skills nativas se descubren por nombre/descripción; se carga el cuerpo al
necesitarlo. De `context-efficiency` solo se incorpora un resumen breve al inicio;
la guía completa queda bajo demanda. Las sesiones que ya arrancaron pueden conservar instrucciones antiguas:
abre una sesión nueva o retoma la existente después de cerrar su CLI para refrescarlas.
Esto no evita que Antigravity tenga que esperar a que se restablezca su cuota.

## Agent Hub

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
Los cuerpos seleccionados siguen sujetos al presupuesto del context pack. La
arquitectura es orientativa: los pendientes generan un aviso y se puede continuar
o definirla primero, sin exigir confirmación por rutina.

Perfiles nuevos, heredando comandos, contenedores y configuración de modelo:

- `antigravity-architect`: worker de arquitectura, con `software-architect`.

No se alteran los perfiles originales ni las policies, aprobaciones o asignaciones
fijas existentes. El registro no ejecuta agentes ni consume cuota. Los perfiles
se usan desde el planificador de Agent Hub, con sus controles sobre repositorio,
permisos y checks. Hermes no recibe
perfiles nuevos de programación desde este instalador. Los perfiles de Hub ya existentes se conservan; no equivalen a sincronizar Hermes.

## Reinstalar o actualizar

```sh
./install.sh agent-skills
# Además de los enlaces y reglas nativas:
dotfiles-agent-skills --hub
# Solo preferencias y contexto de arquitectura locales, sin instalar otros componentes:
dotfiles-agent-skills --architecture-only
# Retirar programación administrada de Hermes, sin tocar sus skills académicas:
dotfiles-agent-skills --remove-hermes-programming dev-podman
```

La instalación es repetible. Conserva reglas personales fuera de sus marcadores;
no sobrescribe skills nativas ajenas con el mismo nombre. Copias de reglas y
perfiles previos en `~/.local/state/dotfiles/agent-skills/`. La limpieza de Hermes
retira las siete skills administradas de `skills/programming/`, los plugins
`dotfiles-architecture` y `dotfiles-context-efficiency`, y solo el bloque
`dotfiles-programming` de SOUL.md. Conserva el resto y mueve lo retirado a
`/opt/hermes/.hermes/backups/remove-programming-<fecha>/`, fuera del descubrimiento
de skills/plugins. Requiere acceso al contenedor; no amplía permisos si falla.
La opción antigua `--hermes` da error y no reinstala programación. Los perfiles
especializados que ya existan se conservan; las seis skills de programación globales del Hub se actualizan desde
su fuente al repetir `--hub`.

Oil UI conserva sus referencias y recursos locales. No consulta versiones ni
envía telemetría; búsqueda o servicios externos requieren autorización expresa.

Validación: frontmatter de las skills, limpieza selectiva de Hermes con fixtures,
instalación repetida, preservación de reglas/skills ajenas, integración de Hub y
context pack real en un worktree temporal sin modelos.

## Memoria externa por directorio, sin Git

Los documentos internos del agente no van en el árbol de código. El almacén es
`~/Documents/Agentes/proyectos/<nombre>-<id>/`, compartido por Codex, Cursor y
Antigravity; Hermes académico queda excluido de estas reglas. El ID se calcula a
partir de la ruta real del directorio, no de `.git`,
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

No hay inyección automática del documento completo: se consulta cuando aporta
contexto. Si la memoria no es accesible o no puede guardarse, distingue persistencia
de diseño pendiente. Conserva la actualización fuera del código en una ubicación
autorizada e informa su ruta; si no hay ninguna, entrega el contenido en el resultado.
Se puede continuar también con decisiones de arquitectura pendientes, indicando los supuestos. No se amplía el sandbox
ni se crean notas dentro del código para satisfacer el control.

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

## Arquitectura proporcional y contexto sin bloqueo

Codex, Cursor y Antigravity reciben la misma política. Exploración, lecturas,
búsquedas, consultas de repositorios, herramientas, dependencias, arquitectura
upstream, baseline de compilación/tests, documentación y borradores no requieren
registro previo. Clonar en un destino autorizado es adquisición que escribe;
no implica aprobación automática ni permiso de publicar.

La arquitectura ausente, en draft, incompleta o con decisiones pendientes genera
un aviso: «Falta definir o actualizar la arquitectura de esta parte. Puedes
continuar con la tarea o definir la arquitectura primero». No es una condición
para implementar ni una confirmación obligatoria. Si el usuario pidió ejecutar,
el agente continúa con el cambio mínimo razonable e indica sus supuestos; si
elige definir primero, prepara ese diseño. Solo pide datos imprescindibles para
cumplir la tarea que no pueda inferir razonablemente. Se respeta upstream, se
consulta el área pertinente y no se rediseña todo por una corrección puntual.
Defined no acredita cobertura; draft y sus pendientes son informativos. No se
inventa arquitectura ni se marca defined para silenciar avisos. Se conserva CAS.

`dotfiles-architecture-guard` aporta recordatorio, ruta, estado y revisión al
inicio de sesión. No clasifica comandos ni herramientas, no los ejecuta y no
responde allow/deny. No considera lectura una adquisición, ni ignora segmentos
posteriores de shell: ha eliminado esa clasificación por completo. Las búsquedas
con comillas, opciones globales de Git, comandos compuestos, redirecciones,
sustituciones y opciones ejecutoras como `rg --pre` quedan bajo permisos y controles
nativos, sin declaraciones engañosas de que sean operaciones de solo lectura.

El instalador migra únicamente sus handlers de arquitectura desde PreToolUse a
SessionStart, preservando otros hooks incluso dentro de un grupo mixto. Codex usa
`hookSpecificOutput/SessionStart/additionalContext`; Cursor `additional_context`;
Antigravity `injectSteps/systemMessage`. Sus contratos PreToolUse no se reutilizan
para autoaprobar. Los recibos de lectura dejan de ser requisito y no se escriben;
sin ID de sesión o con memoria/recibos inaccesibles no hay bloqueo circular. El
contexto no acredita que el agente haya leído o comprendido la arquitectura.

Una revisión nueva orienta la consulta del área afectada; el estado
se vuelve a obtener con `dotfiles-project-context show`. El hook de inicio no
monitoriza cambios de revisión durante una sesión. Sesiones nuevas refrescan
reglas y hooks; no hace falta reiniciar el escritorio. No se modifican controles
sobre secretos, credenciales, publicación/push, destrucción, rutas, dinero ni
servicios externos. Hermes académico no recibe estos hooks; el antiguo plugin
que llama a `check()` queda neutralizado por compatibilidad hasta retirarlo.

Los contratos de Agent Hub son independientes: cambiar estas fuentes no
actualiza por sí solo perfiles o bibliotecas ya registrados en otra instalación.

## Context-efficiency al iniciar sesión

`dotfiles-agent-skills` instala la carga automática sin añadir instrucciones de
uso obligatorio a AGENTS.md. `dotfiles-session-context` lee únicamente la skill
local y extrae únicamente `## Inicio de sesión` (máximo 900 caracteres), sin
inyectar su guía completa. Emite el contrato nativo: SessionStart/additionalContext para Codex,
sessionStart/additional_context para Cursor (conservando sus preferencias previas),
y SessionStart/injectSteps para Antigravity. Codex también vuelve a recibirla al
reanudar o compactar; no hay un hook por mensaje ni un daemon adicional.

El hook existente de inicio de Codex carga también la política vigente desde
`~/.config/agent-skills/AGENTS.md`, que apunta a la fuente mantenida. Indica que
sustituye solo el bloque administrado antiguo y preserva instrucciones ajenas y
permisos nativos. Esto permite recibir las reglas corregidas en una sesión nueva
incluso si `~/.codex/AGENTS.md` está montado como solo lectura. No modifica ese
archivo protegido: su sincronización física y la migración de hooks.json siguen
pendientes hasta ejecutar `--architecture-only` desde un contexto autorizado.
El handler PreToolUse antiguo de Codex responde `{}` sin aprobar ni bloquear.

El plugin de context-efficiency para Hermes ya no se instala: forma parte de la
limpieza selectiva de programación. Se conservan su configuración académica y sus
plugins ajenos. Las sesiones abiertas pueden mantener instrucciones ya cargadas;
tras sincronizar o retirar componentes, abre una sesión nueva.

La carga no prueba obediencia perfecta ni ahorro de tokens. La skill prioriza
exactitud, trabajo completo, verificaciones necesarias y el detalle pedido; para
preguntas cotidianas no exige procedimientos de programación. Si falta el archivo
o supera el límite, el helper informa el error en stderr; no declara una carga
exitosa ni bloquea deliberadamente la sesión. Los hooks anteriores se conservan y
respaldan, y repetir la instalación no duplica los handlers administrados.

Contratos consultados: [Codex](https://learn.chatgpt.com/docs/hooks),
[Cursor](https://cursor.com/docs/hooks), documentación incorporada de Antigravity
(`agy-customizations/docs/hooks.md`). No se inventan campos JSON para Hermes.
