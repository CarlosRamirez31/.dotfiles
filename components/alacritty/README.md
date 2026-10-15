# Alacritty

Este componente instala y registra Alacritty como terminal gráfica de Awesome/X11. El mismo wrapper ofrece una entrada estable para los atajos, Rofi y XDG, con el mismo shell y fuente.

## Qué instala y por qué

| Paquete | Función |
| --- | --- |
| `alacritty` | Emulador de terminal para X11. |
| `zsh` | Shell de login que Alacritty inicia explícitamente. |
| `ttf-jetbrains-mono-nerd` | Fuente monoespaciada con glifos para Starship y herramientas CLI. |
| `noto-fonts-emoji` | Respaldo para emojis de Starship, como el símbolo predeterminado de Kali Linux. |

La configuración elimina decoraciones, usa Catppuccin Mocha con opacidad `0.98`, sin desenfoque, margen de 12 px y JetBrainsMono Nerd Font Regular a 11.5 pt. El cursor vertical parpadeante y la selección se copian al portapapeles; el TOML se recarga sin reiniciar. También envía secuencias estables para borrar con `Ctrl+Backspace`, seleccionar caracteres con `Shift+←/→` y seleccionar palabras con `Ctrl+Shift+←/→`; Zsh interpreta esas secuencias.

## Comandos

```bash
./install.sh alacritty       # instalar solo este componente
dotfiles-terminal            # abrir mediante el wrapper oficial
dotfiles-terminal -e btop    # ejecutar un comando dentro de Alacritty
alacritty --print-events     # diagnóstico de ventanas y entrada
```

`Alt+Enter` y `Ctrl+Alt+T` llaman a `dotfiles-terminal`. En Awesome el wrapper no fuerza `LIBGL_ALWAYS_SOFTWARE`; Alacritty usa X11 y el renderer disponible para VMware.

## Archivos administrados

| Archivo | Propósito |
| --- | --- |
| `.config/alacritty/alacritty.toml` | Ventana, fuente, colores, cursor y Zsh de login. |
| `.local/bin/dotfiles-terminal` | Entrada portable con compatibilidad VMware. |
| `.local/share/applications/Alacritty.desktop` | Registro para Rofi y menús XDG. |
| `.config/xdg-terminals.list` | Declara Alacritty como terminal preferida. |

La fuente depende de `fonts`; el prompt y shell se personalizan en `shell`. Este componente no guarda historial ni configura Zsh.

## Verificación y problemas comunes

```bash
command -v alacritty dotfiles-terminal
grep Alacritty ~/.config/xdg-terminals.list
```

Si faltan iconos, reinstala `fonts` y ejecuta `fc-cache -f`. Si no cargan alias, reinstala `shell` o comprueba `zsh -l`. En Awesome confirma `echo "$XDG_SESSION_TYPE"` (`x11`) y `echo "$WAYLAND_DISPLAY"` (vacío).
