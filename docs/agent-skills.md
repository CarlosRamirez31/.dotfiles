# Skills de programación compartidas

La tarea pendiente de Antigravity quedó implementada con cinco skills locales.
Su fuente es `config/agent-skills/`; no descargan prompts remotos ni cambian modelos.

| Skill | Cuándo se usa |
| --- | --- |
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
- **Hermes:** skills en `/opt/hermes/.hermes/skills/programming/` dentro de
  `dev-podman`. Se añadió un bloque acotado de preferencias de código a su `SOUL.md`,
  conservando su identidad y otras instrucciones. `hermes skills list` las muestra
  como locales y habilitadas.

Las skills nativas se descubren por nombre/descripción; se carga el cuerpo al
necesitarlo. Las sesiones que ya arrancaron pueden conservar instrucciones antiguas:
abre una sesión nueva o retoma la existente después de cerrar su CLI para refrescarlas.
Esto no evita que Antigravity tenga que esperar a que se restablezca su cuota.

## Agent Hub y Coucou

Las cinco se registran en el scope `global` de Agent Hub: llegan a workers y
reviewers en el context pack sin depender de que un CLI cargue su configuración
global. Esta versión del Hub incluye su contenido completo, el texto de las cinco skills
más metadatos; no es carga bajo demanda. Los límites de contexto siguen vigentes.

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
ya existan se conservan; las cinco skills globales del Hub se actualizan desde
su fuente al repetir `--hub`.

Validación: frontmatter de las cinco skills, descubrimiento real de Hermes,
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
