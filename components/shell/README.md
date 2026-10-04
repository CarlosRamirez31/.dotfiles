# Shell

Este componente configura Zsh como shell de login, Oh My Zsh sin tema, Starship Tokyo Night, historial persistente, navegación rápida, búsqueda FZF y herramientas de red. Es la interfaz de terminal común del repositorio.

## Instalación y estructura

```bash
./install.sh shell
reload
```

Instala Zsh, Starship, eza, bat, FZF, fd, ripgrep, zoxide, vivid, plugins de sugerencia/resaltado/historial, utilidades JSON/YAML, red, OpenVPN, SSH, manuales y tldr. Clona Oh My Zsh en `$XDG_DATA_HOME/oh-my-zsh`; si hay una ruta ajena, la respalda. Valida todos los archivos Zsh y cambia el shell de login con `usermod` o `chsh`.

| Archivo | Responsabilidad |
| --- | --- |
| `.zshenv` | PATH portable, editor, pager y socket SSH en todo Zsh. |
| `.zshrc` | Plugins, historial, completado, FZF, zoxide, Starship y Fastfetch. |
| `.config/zsh/aliases.zsh` | Atajos sin argumentos complejos. |
| `.config/zsh/functions.zsh` | Comandos con validación/estado. |
| `.config/zsh/keybindings.zsh` | Borrado y selección de texto mediante teclado. |
| `.config/starship.toml` | Prompt, Git, lenguajes, duración, jobs, hora y estado. |
| `.config/bat/config` | Tema y presentación del visor. |

## Navegación, archivos y desarrollo

| Comando | Uso |
| --- | --- |
| `..`, `...`, `....` | Subir uno, dos o tres directorios. |
| `ls`, `l`, `la`, `ll`, `lt`, `tree` | Listados eza con iconos; `ll` incluye Git y `lt` limita a dos niveles. |
| `cat` / `catp` | Bat legible / `cat` POSIX real. |
| `z RUTA`, `zi` | Saltar a rutas aprendidas / selector interactivo. |
| `mkcd DIRECTORIO` | Crear directorio y entrar. |
| `nv`, `lg`, `py` | Neovim, Lazygit y Python. |
| `serve [PUERTO] [IP]` | HTTP del directorio actual; por defecto `8000` en `127.0.0.1`. |
| `cheat COMANDO` | Página resumida de tldr. |
| `pathlist` | PATH, una entrada por línea. |

FZF: `Ctrl+R` busca historial, `Ctrl+T` archivos y `Alt+C` directorios, con previews de Bat/eza.

La edición de la línea sigue los atajos habituales de un editor gráfico: `Ctrl+Backspace` borra la palabra anterior, `Shift+←/→` amplía la selección por caracteres y `Ctrl+Shift+←/→` la amplía por palabras. Cuando existe una selección, `Backspace` o `Ctrl+Backspace` elimina todo el texto seleccionado. Estas combinaciones están coordinadas con el componente `alacritty`.

## Paquetes y sistema

| Comando | Efecto |
| --- | --- |
| `update` | `sudo pacman -Syu`; actualización completa de Arch. |
| `pacsearch TEXTO` | Buscar repositorios (`pacman -Ss`). |
| `pacinfo PAQUETE` | Información de repositorio (`pacman -Si`). |
| `sysinfo` | Fastfetch. |
| `reload` | Reemplazar el shell actual por un Zsh nuevo. |

Los comandos interactivos de los dotfiles tienen nombres cortos, mientras los scripts internos conservan el prefijo `dotfiles-` para evitar conflictos:

| Comando | Implementación interna |
| --- | --- |
| `doctor` | `dotfiles-doctor` |
| `maintain` | `dotfiles-maintain` |
| `backup` | `dotfiles-backup` |
| `lab-firewall` | `dotfiles-firewall` |
| `htb-target` | `dotfiles-htb-target` |
| `record` | `dotfiles-record` |
| `screenshot` | `dotfiles-screenshot` |
| `clip` / `clip-clear` | Historial y limpieza del portapapeles. |

## Red y laboratorios autorizados

| Comando | Efecto |
| --- | --- |
| `ipa` | Direcciones resumidas. |
| `routes` | Tabla de rutas. |
| `sockets` | Sockets con procesos. |
| `dnsinfo` | Estado de resolución systemd. |
| `portinfo PUERTO` | Filtrar qué socket usa un puerto exacto. |
| `httpheaders URL` | Cabeceras HTTP mediante `curl -I`. |
| `nmap-basic OBJETIVO` | Scripts por defecto y versiones (`-sC -sV`). |
| `nmap-full OBJETIVO` | Todos los puertos, mínimo 1000 paquetes/s. |

Usa Nmap únicamente sobre sistemas propios o autorizados. Para listeners editables: `rlwrap nc -lvnp PUERTO`.

## VPN en segundo plano

```bash
vpn-on /ruta/perfil.ovpn
vpn-off
tail -f "$XDG_RUNTIME_DIR/dotfiles-openvpn.log"
```

`vpn-on` exige exactamente un archivo legible, convierte la ruta a absoluta, cambia el directorio de OpenVPN al del perfil para resolver certificados relativos, daemoniza y guarda PID/log en el runtime. Rechaza iniciar otra sesión administrada. `vpn-off` valida el PID, termina esa sesión y limpia el archivo; no ejecuta un `pkill` global.

## Historial y privacidad

Conserva hasta 100000 entradas en `$XDG_STATE_HOME/zsh/history`, comparte historia entre terminales, elimina duplicados y guarda duración. Prefija un comando sensible con un espacio para que `HIST_IGNORE_SPACE` impida persistirlo.

## Diagnóstico

```bash
zsh -n ~/.zshrc ~/.config/zsh/aliases.zsh ~/.config/zsh/functions.zsh ~/.config/zsh/keybindings.zsh
echo $SHELL
command -v zsh starship fzf zoxide
```
