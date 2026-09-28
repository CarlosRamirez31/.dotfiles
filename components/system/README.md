# System

Prepara la base común que necesitan los demás módulos: red con NetworkManager,
audio PipeWire, portales Wayland, notificaciones, OpenVPN, control de brillo y
teclas multimedia. También instala SDDM cuando no existe otro display manager.

Detecta VMware, VirtualBox y QEMU/KVM para instalar únicamente el agente del
hipervisor activo. NetworkManager queda habilitado inmediatamente; una máquina
nueva puede conectarse antes de iniciar Hyprland.

## Uso

```bash
./install.sh system
systemctl status NetworkManager
```

No contiene personalización visual ni archivos privados.
