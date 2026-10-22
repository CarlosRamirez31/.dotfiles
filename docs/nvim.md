# Neovim

Este componente instala una estación de edición basada en LazyVim, mantenida dentro del mismo historial de dotfiles. Incluye navegación, completado, LSP, formato, Tree-sitter, Git, depuración, Copilot y soporte Flutter para Linux y Windows.

## Dependencias instaladas en Arch

Además de `neovim`, instala Git, ripgrep, fd, FZF, unzip, curl, compiladores (`make`, GCC, CMake), Node/npm, Python/pip, portapapeles X11, Lazygit, .NET SDK, Lua/Luarocks, rust-analyzer y Tree-sitter CLI. Son dependencias usadas por Lazy.nvim, parsers, servidores de lenguaje y plugins nativos.

## Instalación y protección de configuración previa

```bash
./install.sh nvim
```

Si `~/.config/nvim` no apunta a esta copia administrada, el instalador mueve el directorio completo a `nvim.backup.FECHA-HORA`. Esto también elimina de la ruta activa antiguos repositorios Git anidados sin destruirlos. Luego el instalador enlaza la configuración, `Lazy! sync` instala las versiones de `lazy-lock.json` y una tarea instala/verifica todos los parsers declarados.

## Lenguajes y capacidades

El conjunto cubre Bash, C/C++, C#, CMake, CSS, Dart/Flutter, Docker, .NET, Go, GraphQL, HTML, Java, JavaScript/TypeScript/TSX, JSON, Kotlin, Lua, Markdown, PHP, PowerShell, Python, Rust, SQL, Svelte, Swift, TOML, Vue, XML y YAML, además de formatos Git y configuración. LazyVim añade extras para ESLint, Prettier, Tailwind, pruebas, Copilot y utilidades de edición.

## Uso diario

```bash
nv .                       # alias de nvim
nvim archivo
```

| Tecla | Acción personalizada |
| --- | --- |
| `Space` | Líder y menús WhichKey/LazyVim. |
| `ss`, `sv` | Split horizontal/vertical. |
| `sh/sj/sk/sl` | Cambiar entre splits. |
| `Ctrl+w` + flecha | Redimensionar split. |
| `te` | Nueva pestaña. |
| `Tab`, `Shift+Tab` | Pestaña siguiente/anterior. |
| `Ctrl+a` | Seleccionar todo; `+`/`-` incrementa/decrementa. |
| `Space+p/P` | Pegar desde registro 0 sin perder el texto copiado. |
| `Space+c/d` | Cambiar/eliminar sin ensuciar registros. |
| `Space+z` | Zen Mode. |
| `Space+cp` | Panel Copilot. |
| `Space+gk` | Abrir/cerrar LazyDocker en una ventana flotante centrada, como Lazygit. |
| `Space+fu` / `:NvimTrash` | Ver papelera y restaurar un archivo o carpeta en su ruta original. |

### Papelera del explorador (5 horas)

`d` en el explorador lateral de Snacks o en el navegador de Telescope (`sf`) mueve la selección a `~/.local/share/nvim-trash`. En Telescope también funciona `Alt+d` desde inserción. `R` dentro de ambos exploradores abre la lista de recuperación. Los buffers con texto sin guardar se conservan abiertos.

Cada borrado aparece como una sola entrada: un archivo, o una carpeta completa con su contenido. Selecciona una entrada con `Enter` para recuperarla exactamente donde estaba; si su ruta ya está ocupada, se conserva en la papelera y no sobrescribe el archivo nuevo. La lista muestra la ruta original y el tiempo restante.

La retención es de cinco horas desde el borrado, independientemente de la fecha del archivo. En Linux, `nvim-trash-cleanup.timer` comprueba cada minuto y elimina permanentemente solo las entradas vencidas de esta papelera, incluso con Neovim cerrado. Si el equipo está apagado o suspendido, limpia al reanudarse la sesión. El host y `dev-podman` tienen papeleras separadas en sus respectivos homes. En otras plataformas, también se comprueban vencimientos cada minuto mientras Neovim está abierto. Se requiere Python; si falla, el borrado se cancela sin recurrir a eliminación permanente.

Los diagnósticos de LSP se actualizan también en modo inserción, a medida que el servidor publica errores y advertencias.

Flutter añade bajo `Space+d`: hot reload (`dr`), hot restart (`ds`), salir (`dq`), dispositivos (`dd`), logs (`dl`) y emuladores (`de`). La depuración DAP aporta continuar, pausar, step over/into/out, breakpoints, REPL y UI; WhichKey muestra las combinaciones activas.

### Flutter en Android

El SDK se instala con el [componente opcional Flutter](flutter.md): `./install.sh flutter`. Incluye Android SDK, Android Emulator y un AVD; se excluye de la instalación normal y de `all`. El editor descubre el SDK mediante `PATH` o `.fvm/flutter_sdk` en el proyecto. Antes de ejecutar, verifica `flutter doctor -v` y `flutter devices`.

El entorno Flutter se reserva para `dev-podman`. Sus SDKs van en `~/.local/share/flutter-dev/{flutter,android-sdk}`; Zsh solo los añade cuando está instalado el componente opcional y `CONTAINER_ID=dev`. Entra con `dev-podman` y ejecuta Neovim desde allí para que LSP, DAP, Java y ADB compartan el contenedor. Los SDKs, AVDs, cachés y dependencias pertenecen al contenedor. Los proyectos del host se abren desde `/host-home` o `~/Documents`, que está enlazado.

Abre `lib/main.dart` y pulsa `F5`: guarda los archivos, detecta el `pubspec.yaml` más cercano y permite seleccionar el dispositivo para depurar. Durante una sesión, `F5` continúa la ejecución. No se guarda un serial de teléfono ni una ruta de proyecto fija. Se pueden añadir configuraciones propias en `.vscode/launch.json` para entradas alternativas y flavors.

| Tecla | Acción |
| --- | --- |
| `F4` / `Space+dr` | Hot reload; guardar un Dart también recarga automáticamente. |
| `Shift+F4` / `Space+ds` | Hot restart. |
| `F5` | Seleccionar dispositivo y depurar / continuar. |
| `Shift+F5` | Terminar la sesión. |
| `Ctrl+F5` | Repetir la última sesión de depuración. |
| `Ctrl+Shift+F5` | Reiniciar la sesión con DAP. |
| `F9` | Poner/quitar breakpoint. |
| `F10` / `F11` / `Shift+F11` | Step over / into / out. |
| `Space+dp` | Descargar dependencias con pub get. |
| `Space+dW` | Restablecer un emulador: borrar datos y dejarlo apagado, previa confirmación. |

`Space+dW` (W mayúscula) o `:FlutterWipeData` funciona desde cualquier buffer, incluso el inicio de Neovim, sin abrir un archivo Dart ni arrancar previamente el emulador. Lista los AVDs instalados, incluidos los apagados, y pide confirmar el borrado de apps, cuentas y ajustes. Si el seleccionado está abierto, intenta cerrarlo mediante ADB. Después elimina sus discos de datos modificables, caché y snapshots, conservando la definición del dispositivo, y lo deja apagado. No lanza Android para limpiar. Python comprueba el bloqueo del AVD antes de borrar; si sigue en uso, aborta. Si no responde a ADB, ciérralo manualmente y repite la acción. Solo actúa sobre emuladores; no restablece teléfonos físicos. La tarjeta SD virtual, si existe, se conserva. El primer arranque puede tardar.

En el Android activa Opciones de desarrollador y Depuración USB, conecta un cable de datos, desbloquea el teléfono y acepta la autorización RSA. En Arch se necesitan las reglas de `android-udev` y pertenecer a `adbusers` (requiere volver a iniciar sesión tras añadir el grupo). `adb devices -l` debe mostrar `device`; `unauthorized` significa que falta aceptar la autorización en pantalla. `Space+de` usa los emuladores ya creados en el SDK; no instala imágenes ni crea AVDs.

## Administración y diagnóstico interno

```vim
:Lazy
:Lazy sync
:Mason
:checkhealth
:LspInfo
:Copilot auth
```

La configuración desactiva autoformato global por defecto, usa espacios de 2 columnas, líneas sin wrap, búsqueda smart-case, splits abajo/derecha, sin swap y sin mouse. El shell se detecta por plataforma; en Windows prefiere PowerShell 7.

## Windows

```powershell
.\setup\modules\nvim\install.ps1
```

El script usa Winget para Git, Neovim, ripgrep, fd, CMake, Node LTS, .NET 10 y Rustup; instala Tree-sitter con npm, añade rust-analyzer, respalda `%LOCALAPPDATA%\nvim`, copia la configuración y sincroniza plugins/parsers. Flutter busca SDK y emuladores mediante variables/rutas estándar, no un usuario fijo.

## Archivos importantes

`init.lua` carga opciones, keymaps, autocmds y Lazy. `lua/plugins/` contiene extensiones por función; `lua/config/treesitter.lua` es la lista autoritativa de parsers; `lazy-lock.json` fija plugins; `stylua.toml` define formato Lua. Para actualizar conscientemente, ejecuta `:Lazy update`, prueba y revisa el diff del lockfile.

## Fuentes del módulo

Instalador: [`setup/modules/nvim/install.sh`](../setup/modules/nvim/install.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
