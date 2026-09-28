# System

Este es el cimiento del escritorio. Instala servicios y utilidades que otros componentes dan por disponibles: red, audio, portales Wayland, notificaciones, VPN, brillo, multimedia, energía y login gráfico. No contiene personalización visual ni secretos.

## Paquetes base

| Paquete | Responsabilidad |
| --- | --- |
| `networkmanager` | Red cableada, Wi-Fi y perfiles VPN; se habilita inmediatamente. |
| `pipewire`, `pipewire-pulse`, `wireplumber` | Audio moderno y compatibilidad PulseAudio. |
| `xdg-desktop-portal-gtk` | Selector de archivos y portal GTK complementario. |
| `libnotify` | `notify-send` para capturas, grabación y avisos. |
| `openvpn` | Cliente usado por NetworkManager, HyprPanel y `vpn-on`. |
| `brightnessctl` | Brillo desde teclas y gestión de inactividad. |
| `playerctl` | Reproducción multimedia desde teclas físicas. |
| `upower` | Estado de batería y energía para panel/aplicaciones. |
| `pacman-contrib` | Herramientas como `checkupdates` y `paccache`. |
| `git` | Instalación y actualización del repositorio. |

## Display manager y máquinas virtuales

Si no hay `display-manager.service` habilitado, instala y habilita SDDM. Si ya existe GDM, LightDM u otro, lo conserva para no cambiar el login del usuario.

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

NetworkManager se inicia en el acto. SDDM se habilita para el próximo arranque, pero el instalador no termina la sesión actual.

## Verificación y diagnóstico

```bash
systemctl is-enabled NetworkManager.service display-manager.service
systemctl --user status pipewire.service wireplumber.service
journalctl -u NetworkManager.service -b
systemd-detect-virt
```

Tras una instalación completa reinicia y selecciona `Hyprland (uwsm-managed)`. El portal específico de Hyprland viene del componente `hyprland`; la política de suspensión de `session`; y el firewall/keyring de `security`.
