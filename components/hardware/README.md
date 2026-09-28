# Hardware

Instala BlueZ y Blueman para Bluetooth. En una máquina física activa el
servicio; dentro de una VM sin controlador deja el servicio apagado para no
consumir recursos ni mostrar errores inútiles.

En hardware físico también instala FWUPD y Smartmontools, habilitando revisión
de firmware y salud SMART de discos. La administración de batería permanece en
el módulo `session`.

## Uso

```bash
./install.sh hardware
blueman-manager
fwupdmgr get-updates
```

`fwupdmgr` solamente estará presente en hardware físico.
