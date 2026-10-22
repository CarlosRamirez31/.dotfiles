# Rider opcional en dev-podman

```bash
./install.sh rider
./install.sh workbench rider  # requiere dev-podman ya creado
./install.sh all rider
```

Se instala solo al seleccionar `rider` explícitamente. La instalación normal y `all` lo excluyen.

El componente descarga la versión estable oficial de JetBrains, verifica su SHA-256 e instala Rider con su runtime Java incluido bajo `/opt/rider/VERSION` dentro de `dev`. `/opt/rider/current` selecciona la versión activa; las anteriores se conservan. También instala el SDK .NET y el runtime ASP.NET dentro del contenedor para compilar y ejecutar proyectos C#. Las descargas quedan en `~/.cache/rider-dev/setup`.

```bash
dev-podman
cd ~/Projects/mi-proyecto
rider .                      # abrir el directorio actual
rider MiSolucion.sln          # abrir una solución
```

El comando también funciona desde el host: entra en `dev` conservando el directorio actual y los argumentos. Abre Rider en una sesión independiente y devuelve el control a la terminal; puedes cerrarla y el editor sigue abierto. El lanzador termina inmediatamente, sin un supervisor permanente; el init del sistema recoge el proceso cuando sale. La salida del arranque se guarda en `~/.cache/rider-dev/launcher.log`. `rider --version` y `rider --help` mantienen su salida en la terminal.

Los SDKs y las dependencias de Rider se instalan en el contenedor; el host conserva el lanzador y las descargas y preferencias de Rider permanecen en el home interno. Los proyectos del host se abren mediante `/host-home`. La receta `dev-podman setup --fresh` reconstruye la pila completa. En un dev existente, este componente actualiza Rider por separado. La autenticación y la licencia se gestionan en la ventana de Rider.

Comprobaciones sin descargas:

```bash
./install.sh --dry-run all
./install.sh --dry-run rider
python3 tests/rider/test_optional.py
```

## Fuentes del módulo

Instalador: [`setup/modules/rider/install.sh`](../setup/modules/rider/install.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
