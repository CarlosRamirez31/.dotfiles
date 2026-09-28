# Neovim

Este componente instala una estación de edición basada en LazyVim, mantenida dentro del mismo historial de dotfiles. Incluye navegación, completado, LSP, formato, Tree-sitter, Git, depuración, Copilot y soporte Flutter para Linux y Windows.

## Dependencias instaladas en Arch

Además de `neovim`, instala Git, ripgrep, fd, FZF, unzip, curl, compiladores (`make`, GCC, CMake), Node/npm, Python/pip, portapapeles Wayland, Lazygit, .NET SDK, Lua/Luarocks, rust-analyzer y Tree-sitter CLI. Son dependencias usadas por Lazy.nvim, parsers, servidores de lenguaje y plugins nativos.

## Instalación y protección de configuración previa

```bash
./install.sh nvim
```

Si `~/.config/nvim` no apunta a esta copia administrada, el instalador mueve el directorio completo a `nvim.backup.FECHA-HORA`. Esto también elimina de la ruta activa antiguos repositorios Git anidados sin destruirlos. Luego Stow enlaza la configuración, `Lazy! sync` instala las versiones de `lazy-lock.json` y una tarea instala/verifica todos los parsers declarados.

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

Flutter añade bajo `Space+d`: hot reload (`dr`), hot restart (`ds`), salir (`dq`), dispositivos (`dd`), logs (`dl`) y emuladores (`de`). La depuración DAP aporta continuar, pausar, step over/into/out, breakpoints, REPL y UI; WhichKey muestra las combinaciones activas.

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
.\components\nvim\install.ps1
```

El script usa Winget para Git, Neovim, ripgrep, fd, CMake, Node LTS, .NET 10 y Rustup; instala Tree-sitter con npm, añade rust-analyzer, respalda `%LOCALAPPDATA%\nvim`, copia la configuración y sincroniza plugins/parsers. Flutter busca SDK y emuladores mediante variables/rutas estándar, no un usuario fijo.

## Archivos importantes

`init.lua` carga opciones, keymaps, autocmds y Lazy. `lua/plugins/` contiene extensiones por función; `lua/config/treesitter.lua` es la lista autoritativa de parsers; `lazy-lock.json` fija plugins; `stylua.toml` define formato Lua. Para actualizar conscientemente, ejecuta `:Lazy update`, prueba y revisa el diff del lockfile.
