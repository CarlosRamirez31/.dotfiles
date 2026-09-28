# Shell

Instala Zsh, Oh My Zsh y Starship con el estilo Tokyo Night del escritorio.
Agrega sugerencias, resaltado, completado, historial compartido y herramientas
de navegación (`eza`, `zoxide`, `fzf`, `bat`, `fd` y `ripgrep`). También deja
utilidades de red útiles para desarrollo y laboratorios autorizados.

## Comandos diarios

- `z RUTA`: entrar a una ruta aprendida; `zi` permite escogerla con FZF.
- `ll`: listado completo con Git; `lt`: árbol de dos niveles.
- `nv`: Neovim; `lg`: Lazygit; `reload`: recargar Zsh.
- `Ctrl+R`: buscar historial; `Ctrl+T`: buscar archivos; `Alt+C`: directorios.
- `mkcd DIR`: crear un directorio y entrar.
- `serve [PUERTO] [IP]`: servidor HTTP, ligado a localhost por defecto.
- `portinfo PUERTO`: mostrar qué proceso usa un puerto.
- `ipa`, `routes`, `sockets`: resumen de red.
- `nmap-basic IP`: servicios y scripts seguros; `nmap-full IP`: todos los puertos.
- `rlwrap nc -lvnp PUERTO`: listener con historial y edición de línea.
- `cheat COMANDO`: ayuda breve mediante `tldr`.

## Instalación y personalización

```bash
./install.sh shell
```

Los alias están en `.config/zsh/aliases.zsh`, las funciones en
`.config/zsh/functions.zsh` y el prompt en `.config/starship.toml`. La
instalación establece Zsh como shell predeterminado sin reinstalar paquetes ya
presentes.
