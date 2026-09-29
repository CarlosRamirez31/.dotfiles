# Alacritty

Este componente instala y registra Alacritty como la terminal gráfica del escritorio. Existe como punto único de entrada para que Hyprland, HyprPanel, Rofi y XDG abran la misma terminal con el mismo shell, fuente y comportamiento, incluido el ajuste necesario en VMware.

## Qué instala y por qué

| Paquete | Función |
| --- | --- |
| `alacritty` | Emulador de terminal nativo y compatible con Wayland. |
| `zsh` | Shell de login que Alacritty inicia explícitamente. |
| `ttf-jetbrains-mono-nerd` | Fuente monoespaciada con glifos para Starship y herramientas CLI. |
| `noto-fonts-emoji` | Respaldo para emojis de Starship, como el símbolo predeterminado de Kali Linux. |

La configuración elimina decoraciones, usa opacidad `0.94`, desenfoque, margen de 7 px, cursor vertical parpadeante y Tokyo Night. La selección se copia al portapapeles y el TOML se recarga sin reiniciar.

## Comandos

```bash
./install.sh alacritty       # instalar solo este componente
dotfiles-terminal            # abrir mediante el wrapper oficial
dotfiles-terminal -e btop    # ejecutar un comando dentro de Alacritty
alacritty --print-events     # diagnóstico de ventanas y entrada
```

`Alt+Enter` y `Ctrl+Alt+T` llaman a `dotfiles-terminal`. El wrapper activa `LIBGL_ALWAYS_SOFTWARE=1` únicamente en VMware para evitar superficies negras tras cambiar la resolución; en cualquier otro equipo conserva aceleración normal.

## Archivos administrados

| Archivo | Propósito |
| --- | --- |
| `.config/alacritty/alacritty.toml` | Ventana, fuente, colores, cursor y Zsh de login. |
| `.local/bin/dotfiles-terminal` | Entrada portable con compatibilidad VMware. |
| `.local/share/applications/Alacritty.desktop` | Registro para Rofi y menús XDG. |
| `.config/xdg-terminals.list` | Declara Alacritty como terminal preferida. |

La fuente depende de `fonts`; el prompt y shell se personalizan en `shell`; las variables Wayland vienen de `uwsm`. Este componente no guarda historial ni configura Zsh.

## Verificación y problemas comunes

```bash
command -v alacritty dotfiles-terminal
grep Alacritty ~/.config/xdg-terminals.list
```

Si faltan iconos, reinstala `fonts` y ejecuta `fc-cache -f`. Si no cargan alias, reinstala `shell` o comprueba `zsh -l`. En VMware abre mediante `dotfiles-terminal` para aplicar el fallback.
