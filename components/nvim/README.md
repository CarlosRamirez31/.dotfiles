# Neovim

Configuración LazyVim importada del repositorio personal original y unificada
sin historial Git anidado. Funciona en Arch y Windows. Incluye LSP, completado,
formato, depuración, Git, Flutter y Tree-sitter para C#, Python, Rust, Dart,
Lua, JavaScript, TypeScript/TSX, web, shell, SQL y formatos de configuración.

## Movimiento principal

- `h/j/k/l`: movimiento Vim.
- `sh/sj/sk/sl`: cambiar entre splits.
- `ss`: split horizontal; `sv`: vertical.
- `Ctrl+w` más flechas: redimensionar splits.
- `Tab` / `Shift+Tab`: cambiar pestaña.
- `Space`: líder de LazyVim y menús contextuales.

## Comandos realmente usados

```bash
nv .
nvim --headless "+Lazy! sync" +qa
```

Dentro de Neovim, `:Lazy` administra plugins, `:Mason` herramientas de lenguaje
y `:checkhealth` diagnostica el editor. Para Flutter se usan los mapas bajo
`Space+d` mostrados por WhichKey.

## Instalación

```bash
./install.sh nvim
```

En Windows ejecuta `components/nvim/install.ps1`. Flutter busca SDK de Android
y emuladores por variables/rutas estándar, nunca mediante un usuario fijo.
