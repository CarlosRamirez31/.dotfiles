# Hardware

Este componente habilita integración física que no pertenece al compositor: Bluetooth en todos los equipos compatibles y firmware/SMART solo cuando la instalación corre sobre hardware real. Detectar virtualización evita servicios inútiles y alertas falsas dentro de VMs.

## Decisiones automáticas

Siempre instala `bluez` y `bluez-utils`. El panel Bluetooth de Awesome permite buscar, emparejar y conectar dispositivos mediante BlueZ. Habilita `bluetooth.service` si el sistema es físico o si una VM expone un controlador `/sys/class/bluetooth/hci*`.

Cuando `systemd-detect-virt --vm` devuelve `none`, también instala:

- `fwupd` y su timer de actualización de metadatos de firmware;
- `smartmontools` y `smartd.service` para vigilancia de discos.

En una VM sin Bluetooth no activa el servicio. `fwupd` y SMART se omiten porque el hipervisor normalmente no expone firmware/discos físicos de forma útil.

## Uso

```bash
./install.sh hardware
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

Si Bluetooth figura bloqueado, usa `rfkill unblock bluetooth`. `hardware` instala las herramientas pero no administra batería, audio ni teclas multimedia, que pertenecen a `session` y `system`.

## Evitar movimientos del touchpad al escribir

En sesiones Awesome con el controlador Synaptics, `dotfiles-touchpad-typing.service` ejecuta `syndaemon -R -i 0.2 -k`: pausa el touchpad mientras se escribe y lo reactiva 0,2 segundos después de la última tecla. Las teclas modificadoras aisladas no activan la pausa. No modifica el mouse USB/Bluetooth.

Awesome inicia el servicio tras importar DISPLAY y XAUTHORITY. La condición de la unidad evita ejecutarlo cuando Synaptics no está disponible; no cambia el controlador del touchpad. Los sistemas que usan libinput conservan su detección nativa de escritura.

```bash
systemctl --user status dotfiles-touchpad-typing.service
systemctl --user stop dotfiles-touchpad-typing.service
```

Para cambiar el tiempo, modifica el valor de `-i 0.2` en la unidad, ejecuta `systemctl --user daemon-reload` y reinicia el servicio.

## Fuentes del módulo

Instalador: [`setup/modules/hardware.sh`](../setup/modules/hardware.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
