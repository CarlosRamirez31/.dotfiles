# Coucou: personalización local y Agent Hub

Estos dotfiles guardan el tema, hover de Polybar, máscara de entrada del marco de
Awesome, puente de terminal/chat, plugin observador de Hermes y pruebas. No
incluyen el código de Agent Hub, el AppImage de Coucou, conversaciones, archivos
de sesión, credenciales, claves API, sockets ni bibliotecas compiladas.

Coucou y Agent Hub se instalan por separado. Esta personalización no requiere
modificar sus repositorios, hacer push a Coucou ni abrir un PR.

## Restaurar

En Arch deben estar disponibles Python, cc, pkg-config y `webkit2gtk-4.1`.
El módulo Awesome instala los enlaces declarados en `setup/links.tsv`.
Después, con Coucou instalado en `~/.local/opt/coucou/squashfs-root`, ejecutar:

```sh
~/.dotfiles/bin/dotfiles-coucou-setup
```

El script enlaza el código local, conserva las copias anteriores y recompila
la biblioteca del tema de forma atómica. Si falta `agent-hub.json`, crea una
configuración de Alacritty mediante `dotfiles-terminal`; no sobreescribe una
configuración existente. Reiniciar únicamente Coucou para cargar la biblioteca.
No instala ni actualiza aplicaciones y no reinicia el escritorio.

Para restaurar también el plugin en un contenedor Hermes existente:

```sh
~/.dotfiles/bin/dotfiles-coucou-setup --hermes-container dev-podman
```

Los siete hooks son observadores y cargan al iniciar una nueva sesión de Hermes.
El relé de Coucou hacia el contenedor es un socket Unix privado, local. Los hooks
de Codex se gestionan con la integración de Coucou y no se sobreescriben desde
este instalador; el antiguo helper no se vuelve a registrar.

## Asociación y salida

El puente llama exclusivamente al CLI JSON de Agent Hub para consultar rutas.
Cada `(agente, sessionId)` conserva el descriptor completo, sin inferirlo por
fecha, título, carpeta o posición. Los metadatos y rutas privados viven en
`~/.local/share/coucou/agent-hub/`, fuera de Git (directorios 0700, JSON 0600).
Las rutas se escriben atómicamente y se conservan después de abrir la terminal.

`Abrir terminal` valida con `agent-hub open --route-file ABS --dry-run`, y el
controlador local ejecuta los argv separados
`["agent-hub", "open", "--route-file", ABS]`. Al cerrar el CLI normalmente o
mediante Ctrl+C, ejecuta `agent-hub` para volver al selector. Un Ctrl+C que solo
interrumpe una respuesta mantiene el comportamiento del CLI. Los fallos no
seleccionan otra conversación ni crean un reemplazo de una ruta eliminada.
Los bloqueos nativos de sesiones abiertas en otra app se respetan.

Una ejecución antigua con adaptador conocido y sin asociación puede preparar
una conversación general en segundo plano, como autorizó el usuario. Hub exige
un ID real de carpeta; se usa su ubicación general, fuera de repositorios.
Una identidad ambigua requiere selección explícita. No se fuerza ningún lock.

El chat de Coucou usa Codex/Hermes con su autenticación existente y captura el
ID nativo de sus eventos JSON. Los mensajes siguientes continúan ese ID exacto;
las sesiones generales usan un directorio técnico interno y no se añaden a un
proyecto del usuario. «Nuevo chat» archiva la asociación y crea la siguiente
sesión al enviar el primer mensaje. No requiere una API key nueva. La respuesta
se muestra al terminar el turno; adjuntos/permisos interactivos requieren el CLI.

## Pruebas sin modelos

Desde la raíz de dotfiles:

```sh
python3 -B -m unittest discover -s tests/coucou/agent-hub -v
python3 -B -m unittest discover -s tests/coucou -v
node --test tests/coucou/agent-hub/bridge.test.mjs
lua tests/awesome/test_coucou_polybar.lua
```

Los stubs verifican los argv exactos, IDs nativos, Codex/Hermes, alias new/handoff,
Unicode/metacaracteres, bloqueos, errores, doble clic, cancelación y regreso al
selector tras Ctrl+C. La prueba Lua incluye la máscara de entrada del marco de
Awesome, además de la ventana GTK. No se envían prompts reales a los modelos.

## Control de trabajo persistente en Agent Hub

Con Agent Hub 0.5.0, el cliente local añade un botón **Tareas** al selector del
chat. No convierte mensajes normales en tareas ni duplica SQLite. El estado lo
guarda únicamente el motor de Agent Hub. Comandos opt-in desde el chat:

- `/tarea codex Implementar X`: prepara un plan con agente fijo.
- `/tarea hermes Revisar documento`: prepara un plan con Hermes fijo.
- `/tarea auto Investigar X`: permite selección según perfiles configurados.
- `/estado RUN-001` y `/tareas`: consultan estado sin usar un modelo.
- `/ejecutar RUN-001`: solicita ejecutar un plan ya configurado/autorizado.
- `/cancelar RUN-001`: cancela los procesos propios del run.
- `/abrir EXEC-001`: abre por Agent Hub la conversación exacta de esa ejecución.

Durante la ejecución aparece **Detener**, que utiliza el contrato de cancelación
del Hub. El cliente no fuerza locks, no hace merges ni aprueba permisos del
modelo. Las ejecuciones necesitan un repositorio, checks y permisos aprobados;
un plan incompleto se muestra pendiente de humano. `work_control.py` no tiene
almacenamiento de proyectos/tareas: solo invoca el CLI con argv separados.

El código del motor permanece en su repositorio independiente. Estos dotfiles
guardan únicamente el cliente y sus pruebas; `dotfiles-coucou-setup` restaura el
archivo nuevo junto con el puente anterior. No se añaden API keys o servicios.

## Rayita inferior de Flow

Flow crea un dock independiente de la isla superior: su ventana transparente
mide 520×170 aunque la rayita en reposo mide 44×8. Su zona nativa de hover es
más grande que el dibujo, y Awesome añade otro marco que también recibe clics.

La personalización publica los rectángulos visibles de `.capsule` y `.bubble`,
actualizados durante las animaciones. Aplica el mismo contorno al input y a la
forma visual tanto de GTK como del marco de Awesome. En reposo solo la rayita
recibe clics; al abrirse, solo el control/burbuja visibles. Si desaparecen, la
región queda vacía. Los ajustes tardíos del hover nativo no restauran el padding.
No se desactiva Flow ni se modifica Agent Hub.

`native_flow_shape.c` comprueba con WebKit/X11 reales la rayita 44×8, el rechazo
de un reset nativo 96×26, la expansión del control y la región vacía. Usa un
popup fuera de pantalla, sin mover el ratón ni iniciar agentes. La prueba Lua
comprueba además la forma del marco de Awesome y el título vacío sin espacios
finales, que Awesome normaliza. Restaurar con `dotfiles-coucou-setup` y reiniciar
solo Coucou; el módulo Awesome se carga con la configuración habitual.

## Antigravity CLI: sustitución de Gemini CLI

Google retiró el acceso de cuentas personales en Gemini CLI el 18 de junio de
2026. El paquete npm de Gemini CLI se desinstaló y su adaptador local se desactivó;
los perfiles anteriores siguen desactivados como referencia histórica. No se
convirtieron sus IDs en IDs de Antigravity ni se borraron credenciales o historiales.
Antigravity también usa el directorio `~/.gemini/`, que debe conservarse.

Antigravity CLI 1.4.7 se instaló como `~/.local/bin/agy` desde el manifiesto oficial,
verificando SHA512. No se instaló editor, daemon remoto ni proveedor de API. El
motor de Agent Hub permanece independiente de estos dotfiles.

```sh
agy
agent-hub work init --json
~/.dotfiles/bin/dotfiles-coucou-setup --antigravity
```

`agy` inicia el acceso con cuenta de Google en el navegador. Completar allí la
cuenta personal, volver a la terminal y revisar la confianza de la carpeta. Para
salir de una sesión anterior del CLI retirado, usar Ctrl+C en esa terminal antes
de ejecutar `agy`. No compartir códigos de acceso ni contraseñas en un chat.
Para desconectar la cuenta de Antigravity se usa `/logout`, no el `/auth` de Gemini.

El selector de Coucou ofrece Antigravity y acepta `/tarea antigravity ...`.
Captura `init.conversation_id` del protocolo público y espera verificar la
identidad antes de enviar el prompt por stdin JSON. Nunca utiliza `--continue`,
latest ni flags para saltar permisos. La asociación de chat vive en
`chat/antigravity.json`, separada de los chats antiguos.

Los perfiles `antigravity` y `antigravity-reviewer` llaman al driver público
`agent-hub agy-run`. El reviewer usa el esquema estructurado del Hub. Los mensajes,
resultados, rutas y metadatos observados se guardan únicamente en el índice propio
de Agent Hub, `~/.local/state/agent-hub/adapters/antigravity/index.json`. No se
leen SQLite, keyrings, credenciales ni transcripts internos de Antigravity.
La referencia `transcriptPath` del hook puede conservarse sin abrir el archivo.
Las conversaciones abiertas fuera del Hub se incorporan cuando emiten sus hooks;
no se importa automáticamente todo el historial privado preexistente.

Antes de abrir una conversación existente en terminal, Hub hace un probe del
stream público sin enviar un turno; verifica el ID y después pasa exactamente
`agy --conversation ID`. El CLI debe estar autenticado para ese probe. Si falta
la identidad, falla la autenticación o se devuelve otro ID, no se envía el prompt.
Las ejecuciones siguen necesitando repositorio, checks y permisos explícitos.

`--antigravity` restaura seis hooks bajo el nombre `coucou-cli-observer` en
`~/.gemini/config/hooks.json`, preservando otros grupos: SessionStart, PreToolUse,
PostToolUse, PreInvocation, PostInvocation y Stop. El observer registra los IDs
por el CLI público del Hub y reenvía los eventos al relay nativo de Coucou. Antes
de una herramienta devuelve `ask`, que conserva las aprobaciones del CLI, y nunca
`auto_approve`. No modifica modelos ni autenticación.

**Privacidad pendiente de tu cuenta:** en Antigravity, la opción **Enable
Telemetry** de `/config` se guarda en la cuenta, no en settings.json. Después del
login, desactivarla allí si se desea. No se inventó una clave local ni se afirmó
que ya estaba desactivada. El driver del Hub desactiva el auto-update durante sus
procesos con `AGY_CLI_DISABLE_AUTO_UPDATE=true`; no inicia servicios remotos.
