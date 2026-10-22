# Maintenance

Este componente agrupa revisión y limpieza conservadoras para Arch. Está diseñado para informar antes de actuar: no instala actualizaciones automáticamente y nunca elimina paquetes huérfanos por su cuenta.

## Instalación

```bash
./install.sh maintenance
```

Instala `pacman-contrib`, enlaza `dotfiles-maintain` y habilita dos timers de sistema:

- `paccache.timer`: poda periódica de versiones antiguas en la caché Pacman;
- `fstrim.timer`: libera bloques en SSD y almacenamiento thin-provisioned.

## Referencia de comandos

```bash
maintain check
maintain clean
maintain orphans
```

| Subcomando | Comportamiento |
| --- | --- |
| `check` | Lista servicios fallidos de sistema/usuario, uso de `/` y home, y actualizaciones con `checkupdates`. |
| `clean` | Conserva tres versiones de cada paquete en caché y reduce el journal del usuario a 14 días. |
| `orphans` | Lista dependencias huérfanas con `pacman -Qtdq`; no las desinstala. |

Las actualizaciones son deliberadas:

```bash
update                    # alias de sudo pacman -Syu
```

Arch no admite actualizaciones parciales. Separar `checkupdates` de `pacman -Syu` evita cambios desatendidos que requieran intervención al arrancar.

## Verificación y recuperación

```bash
systemctl status paccache.timer fstrim.timer
systemctl list-timers paccache.timer fstrim.timer
journalctl -u paccache.service -u fstrim.service
du -sh /var/cache/pacman/pkg
```

Revisa cuidadosamente la salida de `orphans` antes de usar `pacman -Rns`; una dependencia marcada como huérfana puede seguir siendo útil de forma manual. `clean` no toca archivos personales ni la caché de herramientas de desarrollo.

## Fuentes del módulo

Instalador: [`setup/modules/maintenance.sh`](../setup/modules/maintenance.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
