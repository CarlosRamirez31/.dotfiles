# Hardware

Este componente habilita integración física que no pertenece al compositor: Bluetooth en todos los equipos compatibles y firmware/SMART solo cuando la instalación corre sobre hardware real. Detectar virtualización evita servicios inútiles y alertas falsas dentro de VMs.

## Decisiones automáticas

Siempre instala `bluez`, `bluez-utils` y `blueman`. Habilita `bluetooth.service` si el sistema es físico o si una VM expone un controlador `/sys/class/bluetooth/hci*`.

Cuando `systemd-detect-virt --vm` devuelve `none`, también instala:

- `fwupd` y su timer de actualización de metadatos de firmware;
- `smartmontools` y `smartd.service` para vigilancia de discos.

En una VM sin Bluetooth no activa el servicio. `fwupd` y SMART se omiten porque el hipervisor normalmente no expone firmware/discos físicos de forma útil.

## Uso

```bash
./install.sh hardware
blueman-manager
bluetoothctl
bluetoothctl show
```

Flujo CLI típico:

```text
bluetoothctl
power on
agent on
scan on
pair DIRECCION
trust DIRECCION
connect DIRECCION
```

En hardware físico:

```bash
fwupdmgr get-devices
fwupdmgr refresh
fwupdmgr get-updates
sudo smartctl --scan
sudo smartctl -a /dev/unidad
```

## Servicios y diagnóstico

```bash
systemd-detect-virt --vm
systemctl status bluetooth.service
systemctl status fwupd-refresh.timer smartd.service
rfkill list bluetooth
journalctl -u bluetooth.service -b
```

Si Bluetooth figura bloqueado, usa `rfkill unblock bluetooth`. La applet de Blueman la inicia Hyprland si existe; `hardware` instala las herramientas pero no administra batería, audio ni teclas multimedia, que pertenecen a `session` y `system`.
