# Hyprland

Este componente define el compositor, el modelo de ventanas, monitores, arranque de la sesión gráfica y la gramática global del teclado. Se instala al final porque sus atajos llaman comandos aportados por casi todos los módulos anteriores.

## Paquetes

| Paquete | Función |
| --- | --- |
| `hyprland` | Compositor Wayland y cliente `hyprctl`. |
| `xdg-desktop-portal-hyprland` | Captura de pantalla y portales específicos del compositor. |
| `xorg-xwayland` | Compatibilidad con aplicaciones X11. |
| `hypridle` | Backend de inactividad configurado por `session`. |
| `hyprpolkitagent` | Diálogos gráficos de autorización. |

## Diseño de la configuración

`hyprland.lua` carga tres módulos:

- `lua/core.lua`: monitores, entrada, cursor, cuatro workspaces y arranque;
- `lua/theme.lua`: bordes, espacios y animaciones;
- `lua/binds.lua`: aplicaciones, ventanas, multimedia y sesión.

El cursor de Hyprland permanece visible tanto en hardware físico como en máquinas virtuales. `lua/hardware.lua` detecta VMware únicamente para aplicar sus ajustes gráficos específicos (1920×1080@60, cursor por software, menos efectos y pipelines), sin aplicarlos a otros hipervisores. El cursor usa el tema Bibata; el layout es `dwindle`, el teclado es `us`, el touchpad usa desplazamiento natural y hay cuatro workspaces persistentes.

Al iniciar, finaliza variables UWSM, arranca HyprPanel, Awww, agente Polkit, servicios Cliphist y applet Bluetooth. La autorecarga se deshabilita para no leer archivos Lua a medio actualizar; el instalador ejecuta `hyprctl reload` cuando corresponde.

## Atajos de aplicaciones

| Atajo | Acción |
| --- | --- |
| `Alt+Enter`, `Ctrl+Alt+T` | Terminal. |
| `Alt+Space`, `Alt+D`, `Alt+F2` | Rofi. |
| `Alt+B` | Firefox. |
| `Alt+E` | Thunar. |
| `Super+C`, `Alt+C` | Elegir y pegar desde el historial del portapapeles. |
| `Ctrl+Shift+B` | Bloquear. |
| `Alt+Shift+E` | Finalizar sesión UWSM. |

## Ventanas y workspaces

| Atajo | Acción |
| --- | --- |
| `Alt+H/J/K/L` | Enfocar izquierda/abajo/arriba/derecha. |
| `Alt+Shift+H/J/K/L` | Mover ventana. |
| `Alt+Ctrl+H/J/K/L` | Redimensionar en pasos de 30 px. |
| `Alt+1..4` | Cambiar de workspace. |
| `Alt+Shift+1..4` | Mover ventana y seguirla. |
| `Alt+Q` | Cerrar. |
| `Alt+F` | Pantalla completa. |
| `Alt+V` | Alternar flotante. |
| `Alt` + botón izquierdo/derecho | Arrastrar/redimensionar. |
| Gesto horizontal de tres dedos | Cambiar workspace sin crear nuevos. |

Se usa `Alt` en vez de `Super` para no interceptar atajos del Windows anfitrión en VM.

## Captura, color y multimedia

`Print`, `Alt+Print` y `Alt+Shift+S` capturan completa, región y región editable. `Alt+Shift+R` graba región y `Alt+Shift+C` copia un color. Teclas XF86 controlan volumen, mute, micrófono, brillo y reproducción incluso con la sesión bloqueada.

## Monitores por máquina

```bash
hyprctl monitors all
cp ~/.config/hypr/local.lua.example ~/.config/hypr/local.lua
```

Edita `local.lua` con reglas `hl.monitor`; está ignorado por Git y se carga después de la regla portable. Esto evita subir nombres físicos como `eDP-1` o `DP-1`.

## Instalación y diagnóstico

```bash
./install.sh hyprland
hyprctl reload
hyprctl configerrors
hyprctl clients
journalctl --user -b | rg -i 'hyprland|portal|polkit'
```

El instalador valida errores si Hyprland está activo; fuera de sesión, la configuración carga en el próximo login. Una configuración local errónea puede aislarse renombrando `local.lua` y recargando.
