# System

Este es el cimiento del escritorio. Instala servicios y utilidades que otros componentes dan por disponibles: red, audio, portal GTK para X11, notificaciones, VPN, brillo, multimedia, energía y login gráfico. No contiene personalización visual ni secretos.

## Paquetes base

| Paquete | Responsabilidad |
| --- | --- |
| `networkmanager` | Red cableada, Wi-Fi y perfiles VPN; se habilita inmediatamente. |
| `pipewire`, `pipewire-pulse`, `wireplumber` | Audio moderno y compatibilidad PulseAudio. |
| `xdg-desktop-portal-gtk` | Selector de archivos y portal GTK complementario. |
| `libnotify` | `notify-send` para capturas y avisos. |
| `openvpn` | Cliente usado por NetworkManager y `vpn-on`. |
| `brightnessctl` | Brillo desde teclas y gestión de inactividad. |
| `playerctl` | Reproducción multimedia desde teclas físicas. |
| `upower` | Estado de batería y energía para panel/aplicaciones. |
| `pacman-contrib` | Herramientas como `checkupdates` y `paccache`. |
| `git` | Instalación y actualización del repositorio. |

## Display manager y máquinas virtuales

Instala SDDM y lo selecciona para el próximo arranque. Reemplaza el enlace `display-manager.service` para seleccionar SDDM en arranques futuros sin detener el gestor ni la sesión actuales.

Detecta el hipervisor e instala solo su integración:

| Entorno | Paquete/servicio |
| --- | --- |
| VMware | `open-vm-tools`, `vmtoolsd`, `vmware-vmblock-fuse` |
| VirtualBox | `virtualbox-guest-utils`, `vboxservice` |
| KVM/QEMU | `spice-vdagent` |
| Hardware físico/otro | Ningún agente extra |

## Instalación y uso

```bash
./install.sh system
systemctl status NetworkManager.service
nmcli general status
nmcli device
wpctl status
brightnessctl --list
playerctl status
```

NetworkManager se inicia en el acto. SDDM queda habilitado para el próximo arranque, pero el instalador no termina la sesión gráfica actual.

## Verificación y diagnóstico

```bash
systemctl is-enabled NetworkManager.service display-manager.service
systemctl --user status pipewire.service wireplumber.service
journalctl -u NetworkManager.service -b
systemd-detect-virt
```

Tras una instalación completa reinicia y selecciona `Awesome` en SDDM.

## Fuentes del módulo

Instalador: [`setup/modules/system.sh`](../setup/modules/system.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
