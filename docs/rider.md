# Rider opcional en Distrobox dev

```bash
./install.sh rider
./install.sh workbench rider  # si aún no están Podman y Distrobox
./install.sh all rider
```

Se instala solo al seleccionar `rider` explícitamente. La instalación normal y `all` lo excluyen.

El componente descarga la versión estable oficial de JetBrains, verifica su SHA-256 e instala Rider con su runtime Java incluido bajo `/opt/rider/VERSION` dentro de `dev`. `/opt/rider/current` selecciona la versión activa; las anteriores se conservan. También instala el SDK .NET y el runtime ASP.NET dentro del contenedor para compilar y ejecutar proyectos C#. Las descargas quedan en `~/.cache/rider-dev/setup`.

```bash
distrobox enter dev
cd ~/Projects/mi-proyecto
rider .                      # abrir el directorio actual
rider MiSolucion.sln          # abrir una solución
```

El comando también funciona desde el host: entra en `dev` conservando el directorio actual y los argumentos. Abre Rider en una sesión independiente y devuelve el control a la terminal; puedes cerrarla y el editor sigue abierto. El lanzador termina inmediatamente, sin un supervisor permanente; el init del sistema recoge el proceso cuando sale. La salida del arranque se guarda en `~/.cache/rider-dev/launcher.log`. `rider --version` y `rider --help` mantienen su salida en la terminal.

Los SDKs y las dependencias de Rider se instalan en el contenedor; el lanzador, las descargas y la configuración personal usan el home compartido. Al recrear `dev`, vuelve a ejecutar este componente. La autenticación y la licencia se gestionan en la ventana de Rider.

Comprobaciones sin descargas:

```bash
./install.sh --dry-run all
./install.sh --dry-run rider
python3 tests/rider/test_optional.py
```
