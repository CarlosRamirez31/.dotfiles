# DBeaver opcional en dev

```bash
./install.sh dbeaver
dbeaver
```

Instala DBeaver Community y sus dependencias gráficas/Java dentro de `dev`, solo al seleccionarlo explícitamente. `all` y la instalación normal lo excluyen. El comando funciona desde dentro y fuera de `dev`, devuelve la terminal de inmediato y permite cerrarla sin cerrar el editor.

Las conexiones y preferencias se conservan en el home interno de `dev-podman`. Borrar el contenedor las elimina si no se respaldan. Las credenciales se introducen en DBeaver; no se guardan en los dotfiles. La salida del arranque está en `~/.cache/dbeaver-dev/launcher.log`.

## Fuentes del módulo

Instalador: [`setup/modules/dbeaver/install.sh`](../setup/modules/dbeaver/install.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
