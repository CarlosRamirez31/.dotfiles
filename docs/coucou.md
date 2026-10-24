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
