# HyprPanel

HyprPanel proporciona barra, bandeja, menús rápidos, estadísticas, controles de energía y notificaciones. También integra un indicador específico de Hack The Box sin confundir cualquier VPN con una red HTB.

## Instalación y disposición

Instala `ags-hyprpanel-git` desde AUR y `openvpn`. Las plantillas se copian a `~/.config/hyprpanel` porque HyprPanel necesita archivos reales mutables, no enlaces Stow. Un marcador `.managed-by-dotfiles` identifica el directorio; si encuentra uno ajeno, lo mueve a `.backup.FECHA-HORA` antes de administrarlo.

La barra muestra:

- izquierda: dashboard, título de ventana e indicador HTB;
- centro: cuatro workspaces siempre visibles;
- derecha: volumen, red, RAM, CPU, reloj y notificaciones.

Click derecho del launcher abre Rofi y click central abre terminal. El panel usa Lexend, paleta Catppuccin, barra flotante y notificaciones arriba a la derecha. Sleep ejecuta `dotfiles-sleep`, respetando la protección de VMs del componente `session`.

## Estado HTB

`dotfiles-htb-vpn-status` revisa interfaces `tun*`/`tap*`, dirección IPv4 y rutas `10.10.*` o `10.129.*`. Solo entonces produce JSON para el módulo. De esta forma una VPN de trabajo normal no aparece como HTB.

```bash
dotfiles-htb-vpn-status
dotfiles-htb-target 10.10.11.20
dotfiles-htb-target
dotfiles-htb-target clear
```

El objetivo se valida como IPv4 y se guarda en el estado local del usuario. Cuando existe, el panel muestra esa IP como “Objetivo activo”; de lo contrario muestra la IP VPN. `clear` elimina únicamente el objetivo, no desconecta OpenVPN.

## Archivos

| Archivo | Función |
| --- | --- |
| `templates/config.json` | Layout, menús, notificaciones, tema y acciones. |
| `templates/modules.json` | Definición del módulo HTB y sondeo. |
| `templates/modules.scss` | Apariencia del módulo personalizado. |
| `.local/bin/dotfiles-htb-vpn-status` | Detección VPN/HTB y salida JSON. |
| `.local/bin/dotfiles-htb-target` | Gestión del objetivo local. |

## Reinicio y diagnóstico

```bash
./install.sh hyprpanel
pkill -x hyprpanel
uwsm-app -- hyprpanel
tail -f "${XDG_RUNTIME_DIR:-/tmp}/hyprpanel-dotfiles.log"
```

Durante una sesión activa el instalador detiene Waybar, cierra HyprPanel y lo inicia mediante UWSM cuando está disponible. Si falta el indicador, comprueba `ip -br address`, `ip route`, el estado JSON y que la VPN realmente tenga rutas HTB.
