# Podman con home interno

Estos perfiles son independientes de Distrobox. No sustituyen comandos, contenedores ni perfiles existentes. Requieren Podman rootless con crun y Python 3 en el host; las herramientas de trabajo se instalan dentro de los contenedores.

| Perfil | Contenedor nuevo | Contenido |
| --- | --- | --- |
| dev | dev-podman | Copia inicial de los paquetes y `/opt` de `dev`; copia interna de Flutter, Android/AVD, Neovim, Rider y preferencias de desarrollo. |
| parrotos | parrotos-podman | Parrot Security con Neovim/LazyVim, Zsh, Starship y utilidades de terminal. Sin añadir Flutter, Rider, DBeaver ni servidores de bases de datos. |
| kali | kali-podman | Kali con la selección de herramientas de laboratorio declarada y la misma base de terminal/editor. |

## Preparar y entrar

Desde la terminal del host:

```bash
~/.local/bin/dotfiles-podman setup all
~/.local/bin/dotfiles-podman enter dev
~/.local/bin/dotfiles-podman enter parrotos
~/.local/bin/dotfiles-podman enter kali
~/.local/bin/dotfiles-podman status all
~/.local/bin/dotfiles-podman verify all
```

`setup` no reemplaza contenedores. Rechaza un nombre ocupado por otro administrador. Si la preparación falla, se puede repetir el mismo comando; después de copiar el home se conserva un marcador para no volver a sobrescribirlo. En un entorno ya preparado solo verifica su funcionamiento.

El home interno conserva la ruta `/home/USUARIO` para que las rutas absolutas de Android, AVD, Rider y sus configuraciones sigan siendo válidas. No es un montaje ni un volumen: los nuevos archivos de ese home pertenecen al sistema de archivos del contenedor. El home real se monta explícitamente con lectura/escritura en `/host-home`:

```bash
cd /host-home/Projects/mi-proyecto
nvim .
```

La receta de dev enlaza `~/Documents` completo a `/host-home/Documents`, incluyendo Programacion, Universidad y todas sus otras carpetas. Para aplicar el enlace desde una sesión existente dentro de dev-podman:

```bash
python3 /host-home/.dotfiles/components/workbench/podman/share_documents.py
```

Si antes había un Documents interno, se conserva dentro del contenedor en `~/.local/state/podman-workbench/documents-before-share-*`. El enlace no sobrescribe documentos del host y se puede aplicar de nuevo sin duplicar respaldos. `dotfiles-podman integrate dev` también aplica este cambio desde el host.

Lo guardado en `/host-home` modifica archivos reales y permanece al borrar el contenedor, incluyendo dependencias y compilaciones que se creen dentro de proyectos. Para mantener también los resultados de compilación dentro del contenedor, trabaja en una copia interna del proyecto y exporta solo los resultados que quieras conservar.

La copia inicial de `dev` no mueve ni borra originales. Usa `podman commit --pause=false --include-volumes=false`: no pausa el contenedor original y no incorpora sus montajes. Después copia únicamente las rutas de configuración y desarrollo declaradas en `BASE_COPY` y `DEV_COPY`; materializa los enlaces de los dotfiles para que el nuevo home no dependa del antiguo. No copia todo el home, las bases de datos externas ni carpetas de Podman. Si un emulador o programa está escribiendo durante la copia, sus datos no constituyen un respaldo consistente de una aplicación detenida.

## Volver a instalar programas

Las recetas viven en `profiles.json`, `dev-packages.txt`, `prepare.sh`, `finish.sh` y los componentes opcionales existentes del repositorio. No se necesita conservar el contenedor original para reconstruir:

```bash
# Solo cuando dev-podman no exista: reconstrucción desde Arch y sus instaladores.
~/.local/bin/dotfiles-podman setup dev --fresh
# Repetir las recetas de seguridad cuando sus contenedores no existan.
~/.local/bin/dotfiles-podman setup parrotos
~/.local/bin/dotfiles-podman setup kali
```

`--fresh` se ejecuta desde una terminal interactiva para que puedas revisar las licencias de Android. Instala los paquetes registrados y ejecuta los instaladores de Docker CLI, DBeaver, Rider, Flutter/Android y Hermes dentro del contenedor nuevo. Los dotfiles versionados aportan configuraciones iniciales aunque las copias antiguas del home ya no existan. Las descargas siguen las versiones estables/repositorios que seleccionan esos instaladores; esto reproduce los programas y la configuración declarada, no congela todas las versiones futuras.

Una receta no reconstruye sesiones, bases de datos ni datos del teléfono virtual eliminados sin respaldo. Para conservarlos, respalda el home interno y `/opt` por separado. Usa GNU tar con `--sparse` para los discos de Android: un `podman commit` de esos discos puede expandir sus espacios vacíos y agotar el directorio temporal. Los respaldos e imágenes pueden contener credenciales y datos personales; son archivos privados, no imágenes para publicar.

## Gráficos y servicios

Al crear el contenedor se conectan los sockets disponibles de X11/Wayland y audio; `dev` recibe KVM cuando existe y los perfiles reciben `/dev/dri` cuando está disponible. X11 comparte solamente el socket del display padre y conserva un directorio privado para Xephyr. La autorización se copia al home interno y se renueva al entrar, sin depender de un archivo temporal del host montado permanentemente. No se usa `xhost` ni modo privilegiado. La conexión gráfica requiere una sesión gráfica y una autorización válidas.

En `dev` se comparte el bus de sesión en `/host-session/bus` para la integración con Awesome. La copia de `presentacion` lanza su terminal privada directamente dentro del nuevo contenedor y sus atajos invocan `podman exec dev-podman`, con comprobación del proceso dentro de su propio espacio de PIDs. Al salir de Hermes restaura los atajos. Los scripts originales de Distrobox no se modifican. Las fuentes del escritorio también se instalan dentro de `dev`.

```bash
dotfiles-podman exec dev -- rider
dotfiles-podman exec dev -- dbeaver
dotfiles-podman exec dev -- flutter-emulator
# O desde una sesión de dotfiles-podman enter dev:
presentacion iniciar
presentacion hermes
```

Abre tus proyectos usando `/host-home/...`; el home interno conserva espacio separado para herramientas y ajustes.

La red usa el modo rootless predeterminado de Podman. Los servicios del host se acceden según su configuración mediante `host.containers.internal`; `localhost` se refiere al contenedor nuevo. Las bases de datos ejecutadas en otros contenedores permanecen separadas y no se duplican automáticamente.

Docker, Compose y LazyDocker de `dev` usan el Podman rootless existente del host. `integrate dev` configura un socket local de systemd que reenvía al socket existente, sin instalar paquetes en el host ni recrear contenedores. Los dos archivos de unidad quedan en `~/.config/systemd/user/workbench-podman.*`, y la conexión en `~/.local/state/podman-workbench/docker.sock`, accesible desde `/host-home`. Es el mismo motor y permite administrar también los contenedores anteriores: no constituye una separación de permisos.

Los servicios creados con Compose y sus volúmenes pertenecen al motor del host; borrar `dev-podman` no los elimina. Usa nombres de proyecto propios, por ejemplo `docker compose -p dev-podman-miapp up -d`; cuando autorices borrar esos datos, `docker compose -p dev-podman-miapp down --volumes` elimina los recursos de ese proyecto. Los bind mounts se resuelven en el host: usa la ruta real `/home/USUARIO/...` del host en la configuración de volúmenes, aunque edites el proyecto desde `/host-home/...`. Un archivo que existe solamente en el home interno no puede montarse mediante el motor del host.

Para aplicar o repetir la integración en el dev existente:

```bash
dotfiles-podman integrate dev
```

Este paso conserva los programas y el home interno. Copia dentro de `dev` los temas Bibata y Oranchelo del host y las preferencias GTK; instala únicamente dentro de `dev` las utilidades X11 necesarias. El escritorio virtual usa el fondo actual del host al aplicar la integración, y `Alt+w` permite elegir otros desde la carpeta existente `Pictures/Wallpapers`, accesible mediante un enlace a `/host-home`. Las selecciones posteriores del escritorio virtual se guardan dentro del contenedor. Neovim conserva las configuraciones y estilos copiados, con plugins y cachés internos; no instala herramientas en el host.

Los accesos al home real, pantalla y dispositivos son explícitos. Esta disposición organiza y elimina las instalaciones con el contenedor; no ofrece aislamiento de seguridad frente a código hostil que pueda acceder a `/host-home`.

## Borrado posterior

La creación de perfiles no realiza limpieza, poda ni reemplazos. El antiguo dev y su copia temporal se retiraron por autorización explícita después de comprobar la migración. Cuando se decida borrar uno de los nuevos contenedores, su home interno desaparece con él; `/host-home` permanece. Las imágenes base y la imagen inicial `localhost/workbench-dev-snapshot:initial` tienen su propio ciclo de vida y no desaparecen por borrar el contenedor.

## Cliente remoto de Podman

El lanzador usa `podman` por defecto. Para un cliente remoto explícito admite `PODMAN_WORKBENCH_CLIENT`, por ejemplo `podman --remote --url unix:///run/user/1000/podman/podman.sock`. Solo debe apuntar al motor rootless del usuario que comparte este home. No cambia automáticamente de motor ni usa sudo.

## Verificación de las recetas

```bash
python3 -B components/workbench/tests/test_podman_workbench.py
bash -n components/workbench/podman/{prepare,finish,verify}.sh
```

Parrot Echo ofrece Neovim 0.10 y Tree-sitter 0.22 en sus repositorios. El bootstrap incorpora Neovim oficial 0.12.6 verificado por SHA-256, Tree-sitter CLI 0.27.1 y Yazi 26.9.1 cuando los paquetes disponibles no cumplen los requisitos. Estas versiones están registradas en `finish.sh`; los repositorios de APT no se mezclan.

## Copias de migración

El Distrobox `dev`, sus volúmenes anónimos y la copia temporal `dev-podman-migracion` se retiraron después de verificar las copias internas y arrancar Android sin los SDKs del host. También se eliminaron los SDKs, AVDs, cachés y datos de desarrollo correspondientes del home real. Las preferencias antiguas de Rider que diferían y un respaldo de la base de sesiones de Hermes se conservaron dentro del nuevo dev, en `~/.local/state/podman-workbench/retired-dev`.

Se conservan apagadas las copias de seguridad `parrotos-podman-migracion` y `kali-podman-migracion`; los entornos de seguridad anteriores permanecen sin borrar. Las imágenes compartidas que usa el dev nuevo se conservan.

Los lanzadores del host utilizan `dotfiles-dev-exec` para entrar al nuevo entorno y mapear el directorio actual a `/host-home`. Los instaladores opcionales se dirigen al dev nuevo; el manifiesto Distrobox ya no contiene un perfil dev.
