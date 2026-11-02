# Podman con home interno

Estos perfiles son independientes de Distrobox. No sustituyen comandos, contenedores ni perfiles existentes. Requieren Podman rootless con crun y Python 3 en el host; las herramientas de trabajo se instalan dentro de los contenedores.

| Perfil | Contenedor nuevo | Contenido |
| --- | --- | --- |
| dev | dev-podman | Copia inicial de los paquetes y `/opt` de `dev`; copia interna de Flutter, Android/AVD, Neovim, Rider y preferencias de desarrollo. |
| parrotos | parrotos-podman | Parrot Security con Neovim/LazyVim, Zsh, Starship y utilidades de terminal. Sin añadir Flutter, Rider, DBeaver ni servidores de bases de datos. |
| kali | kali-podman | Kali con la selección de herramientas de laboratorio declarada y la misma base de terminal/editor. |

Ejecuta los comandos desde una terminal del host, con tu usuario normal y sin `sudo`. Los nombres de perfil usados por el lanzador son `dev`, `parrotos` y `kali`; los nombres completos de Podman son los de la tabla. Si ya tienes tus entornos creados, puedes pasar al apartado 2 para aplicar ajustes o al 3 para entrar.

## 1. Crear el contenedor

### 1.1. Crear manualmente con Podman

Esta alternativa crea un contenedor adicional con home interno y acceso al home real en `/host-home`. Elige **uno** de estos bloques según la distribución; los nombres de ejemplo no sustituyen tus entornos actuales.

Arch básico:

```bash
contenedor=dev-ejemplo
imagen=docker.io/library/archlinux:latest
```

Parrot básico, con las herramientas que ya contiene su imagen Security:

```bash
contenedor=parrotos-ejemplo
imagen=docker.io/parrotsec/security:latest
```

Kali básico:

```bash
contenedor=kali-ejemplo
imagen=docker.io/kalilinux/kali-rolling:latest
```

Después del bloque elegido, ejecuta este comando común:

```bash
podman pull "$imagen"

# create prepara el contenedor; todavía no lo inicia.
podman create \
    --name "$contenedor" \
    --hostname "$contenedor" \
    --userns=keep-id \
    --user "$(id -u):$(id -g)" \
    --init \
    --image-volume=ignore \
    --mount "type=bind,source=$HOME,destination=/host-home,rw" \
    --env "HOME=$HOME" \
    --workdir / \
    --entrypoint /usr/bin/sleep \
    "$imagen" infinity
```

`create` prepara el contenedor y sus montajes. Todavía no lo inicia ni instala tus preferencias. `podman run` combina crear e iniciar; aquí usamos los pasos separados. El proceso `sleep infinity` lo mantendrá encendido mientras abres y cierras terminales. Para reproducir los SDKs, estilos e integración gráfica de tus entornos actuales, usa la alternativa del apartado 1.2.

### 1.2. Crear tus entornos completos con las recetas

Esta alternativa reproduce tus tres perfiles personales, incluyendo sus programas y configuraciones. No requiere crear los contenedores de ejemplo ni ejecutar previamente el apartado manual.

Las recetas viven en `profiles.json`, `dev-packages.txt`, `prepare.sh`, `finish.sh` y los componentes opcionales existentes del repositorio. No se necesita conservar el contenedor original para reconstruir:

```bash
# Solo cuando dev-podman no exista: reconstrucción desde Arch y sus instaladores.
dev-podman setup --fresh
# Repetir las recetas de seguridad cuando sus contenedores no existan.
parrotos-podman setup
kali-podman setup
```

`--fresh` se ejecuta desde una terminal interactiva para que puedas revisar las licencias de Android. Instala los paquetes registrados y ejecuta los instaladores de Docker CLI, DBeaver, Rider, Flutter/Android y Hermes dentro del contenedor nuevo. Los dotfiles versionados aportan configuraciones iniciales aunque las copias antiguas del home ya no existan. Las descargas siguen las versiones estables/repositorios que seleccionan esos instaladores; esto reproduce los programas y la configuración declarada, no congela todas las versiones futuras.

`setup` no reemplaza contenedores. Rechaza un nombre ocupado por otro administrador. Si la preparación falla, se puede repetir el mismo comando; después de copiar el home se conserva un marcador para no volver a sobrescribirlo. En un entorno ya preparado solo verifica su funcionamiento.

## 2. Configurar el entorno y las carpetas compartidas

### 2.1. Configurar el ejemplo manual

Si elegiste el apartado 1.1, continúa en la misma terminal del host para conservar la variable `contenedor`. Primero inicia su proceso para poder ejecutar los comandos de configuración. Todos los paquetes de este bloque se instalan dentro del contenedor.

```bash
podman start "$contenedor"

# Crear el home privado con tu UID/GID.
podman exec --user 0 "$contenedor" \
    install -d -o "$(id -u)" -g "$(id -g)" "$HOME"

# Instalar una shell y un editor con el gestor de esa distribución.
podman exec --user 0 "$contenedor" sh -c '
    if command -v pacman >/dev/null; then
        pacman -Syu --needed --noconfirm zsh neovim
    else
        apt-get update && apt-get install -y zsh neovim
    fi
'

# Enlazar Documents completo con el host.
podman exec --user "$(id -u):$(id -g)" "$contenedor" \
    sh -c 'test -e "$HOME/Documents" || test -L "$HOME/Documents" || ln -s /host-home/Documents "$HOME/Documents"'
```

El ejemplo queda con Zsh y Neovim básicos. Los estilos, plugins, SDKs e integración gráfica de tus entornos personales se preparan mediante las recetas del apartado 1.2. No ejecutes `integrate` sobre los contenedores de ejemplo: ese comando valida los perfiles administrados por estas recetas.

### 2.2. Configurar tus tres entornos personales

`setup` ya incluye la configuración inicial. Para aplicar los ajustes actuales a contenedores existentes, sin recrearlos:

```bash
dev-podman integrate
parrotos-podman integrate
kali-podman integrate
```

En dev se configura la conexión al Podman del host, Documentos y la apariencia del escritorio virtual. Este paso conserva los programas y el home interno. Copia dentro de `dev` los temas Bibata y Oranchelo del host y las preferencias GTK; instala únicamente dentro de `dev` las utilidades X11 necesarias. El escritorio virtual usa el fondo actual del host al aplicar la integración, y `Alt+w` permite elegir otros desde la carpeta existente `Pictures/Wallpapers`, accesible mediante un enlace a `/host-home`. Las selecciones posteriores del escritorio virtual se guardan dentro del contenedor. Neovim conserva las configuraciones y estilos copiados, con plugins y cachés internos; no instala herramientas en el host.


En Parrot y Kali, estos comandos actualizan las preferencias internas del perfil indicado: Zsh y sus atajos, Starship, colores de archivos, Fastfetch, Yazi, Bat, Lazygit y preferencias GTK/cursor. Copian los temas Bibata y Oranchelo disponibles en el host y conservan su propio estado dentro de cada contenedor. No instalan programas en el host ni añaden SDKs de programación, bases de datos, Rider, Flutter o Hermes. La configuración actual de Neovim, sus plugins y su caché se conservan.

`~/Documents` se enlaza completo a `/host-home/Documents`; `~/Pictures/Wallpapers` da acceso a la colección existente. Si había documentos internos, se guardan aparte antes de crear el enlace. Las preferencias que se sustituyan se respaldan en `~/.local/state/podman-workbench/preferences-before-security`, dentro del contenedor. Tras aplicar, abre una nueva terminal o ejecuta `exec zsh -l`.

El formato hexadecimal `#RRGGBB` de Fastfetch requiere la versión 2.42 o posterior. Los perfiles de seguridad usan los mismos colores RGB escritos como secuencias ANSI SGR, para admitir también versiones anteriores. Véase la [especificación oficial de colores](https://github.com/fastfetch-cli/fastfetch/wiki/Color-Format-Specification). La verificación ejecuta Fastfetch explícitamente, porque su arranque automático se omite cuando no hay una terminal interactiva.

`integrate` no crea otro escritorio ni adapta las herramientas de presentación de Hermes en estos perfiles. Las aplicaciones gráficas usan los sockets disponibles con los que se creó cada contenedor.

El home interno conserva la ruta `/home/USUARIO` para que las rutas absolutas de Android, AVD, Rider y sus configuraciones sigan siendo válidas. No es un montaje ni un volumen: los nuevos archivos de ese home pertenecen al sistema de archivos del contenedor. El home real se monta explícitamente con lectura/escritura en `/host-home`.

Las recetas de los tres perfiles enlazan `~/Documents` completo a `/host-home/Documents`, incluyendo Programacion, Universidad y todas sus otras carpetas.

Si antes había un Documents interno, se conserva dentro del contenedor en `~/.local/state/podman-workbench/documents-before-share-*`. El enlace no sobrescribe documentos del host y se puede aplicar de nuevo sin duplicar respaldos. Los comandos `integrate` del apartado 2.2 también aplican este cambio desde el host.

Lo guardado en `/host-home` modifica archivos reales y permanece al borrar el contenedor, incluyendo dependencias y compilaciones que se creen dentro de proyectos. Para mantener también los resultados de compilación dentro del contenedor, trabaja en una copia interna del proyecto y exporta solo los resultados que quieras conservar.

## 2.3. Montajes opcionales en Kali y Parrot

La función está desactivada por defecto. Desde el **anfitrión**, como usuario normal:

```bash
lab-mount enable       # Activar/actualizar para Kali y Parrot; prepara el host con sudo.
lab-mount status
lab-mount disable
```

El lanzador se instala con el componente `workbench`; también puedes ejecutar
`~/.dotfiles/bin/lab-mount`. La activación configura los dos perfiles, sin modificar dev
ni Distrobox. Si ya activaste una versión anterior, repite `lab-mount enable` para instalar
el puente actualizado en ambos. No hace falta registrar cada origen ni editar fstab.

Después de activar, **dentro de Kali o Parrot**, usa los comandos habituales:

```bash
# SMB/CIFS: solicita la contraseña en la terminal.
sudo mount -t cifs '//IP_DEL_TARGET/Company Data' /mnt/montajes/company \
  -o username=htb-student

# NFS.
sudo mount -t nfs SERVIDOR:/export/data /mnt/montajes/nfs -o vers=4

# ISO guardada en el home compartido del anfitrión; siempre se monta en solo lectura.
sudo mount -o loop /host-home/Downloads/lab.iso /mnt/montajes/iso

# USB: usa el nombre real del dispositivo del anfitrión (compruébalo allí con lsblk -f).
sudo mount -t exfat /dev/sdb1 /mnt/montajes/usb

ls /mnt/montajes/company
sudo umount /mnt/montajes/company
lab-mount list
```

El puente crea el destino automáticamente: debe ser una **subcarpeta directa** de
`/mnt/montajes`, con letras, números, guiones o guiones bajos. No uses Desktop, `/`,
`/mnt/montajes` a secas ni destinos anidados. El anfitrión monta realmente el recurso en
`/srv/workbench-mounts/NOMBRE`; Kali y Parrot ven el mismo montaje. Desmontarlo en uno lo
retira de ambos. Las credenciales y permisos del servidor siguen siendo necesarios.

Se admiten `cifs`, `nfs`, `nfs4`, `iso9660`, `udf`, `ext4`, `vfat`, `exfat`, `ntfs3` y
`auto` para dispositivos extraíbles. El tipo puede inferirse para `//servidor/recurso`,
`servidor:/recurso`, archivos `.iso` y dispositivos. Las imágenes locales deben estar en
`/host-home/`: el home privado del contenedor no es el home del anfitrión. Los dispositivos
se comprueban en el anfitrión y deben ser extraíbles/USB; se rechazan discos internos y
cualquier dispositivo ya montado fuera de la carpeta autorizada.

Las herramientas del sistema de archivos deben existir **en el anfitrión**, por ejemplo
en Arch: `sudo pacman -S --needed cifs-utils nfs-utils` para SMB y NFS. El kernel del host
debe admitir el tipo de sistema de archivos; esto no convierte cualquier protocolo en
un montaje soportado. SSHFS, por ejemplo, utiliza su propio cliente y no se incluye aquí.

Los wrappers se instalan en `/usr/local/sbin/mount` y `/usr/local/sbin/umount` dentro del
contenedor, y una regla `secure_path` permite que `sudo mount` los encuentre. Las operaciones
fuera de `/mnt/montajes` y el listado normal sin argumentos se pasan a las herramientas
nativas del contenedor, sin otorgarles permisos del host. Invocar `/usr/bin/mount` o
`/bin/mount` explícitamente también usa la herramienta nativa, sin el puente.

El puente acepta `-t`, `-o`, `-r`, `-w`, `-v` y dos argumentos para montar; para desmontar,
acepta el destino y `-v`. Valida cada opción según el tipo, fuerza `nosuid,nodev`, y rechaza
`bind`, `remount`, cambios de propagación, ayudantes arbitrarios y desmontajes forzados o
diferidos. No añade `--privileged`, `SYS_ADMIN` ni un socket de Podman/Docker.

En CIFS se aceptan `username=`, `password=`, `domain=` y sus alias, o un archivo
`credentials=` que pueda leer tu usuario dentro del contenedor. Si falta contraseña y
no usas `guest`, la pide por terminal. La contraseña se transmite por el socket local y
por stdin al helper, y se guarda temporalmente en un archivo root 0600 mientras monta;
no se añade a los argumentos del proceso privilegiado ni a la lista persistente.
Si tú escribes `password=` en el comando original, puede quedar en el historial y en los
argumentos de ese comando; usa el prompt o un archivo de credenciales protegido.

El anfitrión mantiene un subárbol compartido y los contenedores lo reciben con `rslave`.
El broker systemd del usuario verifica `SO_PEERCRED` y solo delega solicitudes validadas
al helper root; este repite la validación y mantiene los destinos bajo control de root.
El wrapper baja al UID del usuario que invocó sudo antes de conectar. Las imágenes se
abren con los permisos de ese usuario y el dispositivo loop se configura directamente
con ese descriptor, en solo lectura y con liberación automática. Esto requiere Linux 5.8
o posterior y soporte loop en el host (`sudo modprobe loop` si no está cargado).
La autorización pertenece al usuario del host: sus programas pueden
solicitar las mismas operaciones. El fstab separado de versiones anteriores se conserva
como función opcional para nombres registrados con `lab-mount mount NOMBRE`; no es
necesario para los comandos normales.

Cambiar el bind mount requiere detener brevemente y recrear cada contenedor, conservando
su rootfs y home interno. Los originales se guardan detenidos como
`NOMBRE-before-mounts-ID`, junto con imágenes de respaldo; no se eliminan. Se conserva su
estado encendido/apagado. Cierra las tareas activas antes de cambiar el interruptor: los
procesos en ejecución no forman parte del snapshot. Se rechazan homes, volúmenes externos
y binds personalizados que no puedan conservarse automáticamente. Una actualización del
puente con el bind ya presente no requiere crear otro snapshot.

`disable` desmonta los recursos, desactiva los servicios y retira el bind y los wrappers
de ambos contenedores. Si un montaje está ocupado, cierra los archivos o terminales que
lo usan y repite el comando; no se fuerza el desmontaje. Conserva la configuración opcional
y los respaldos. Si falla una migración, conserva el original y muestra el diagnóstico;
revisa `lab-mount status` antes de reintentar.

Requiere Podman local y systemd. Referencias: [propagación en Podman](https://docs.podman.io/en/stable/markdown/podman-run.1.html),
[opciones de mount](https://man7.org/linux/man-pages/man8/mount.8.html) y
[credenciales CIFS](https://docs.kernel.org/admin-guide/cifs/usage.html).
Las pruebas no realizan montajes reales ni sustituyen la comprobación posterior a activar.

## 3. Iniciar y entrar

Estos son los comandos originales para los tres entornos ya creados y configurados:

```bash
# Iniciar los tres. También puedes indicar solo un nombre.
podman start dev-podman parrotos-podman kali-podman

# Entrar en dev.
podman exec --user "$(id -u):$(id -g)" --workdir "$HOME" -it dev-podman zsh -l

# Entrar en Parrot.
podman exec --user "$(id -u):$(id -g)" --workdir "$HOME" -it parrotos-podman zsh -l

# Entrar en Kali.
podman exec --user "$(id -u):$(id -g)" --workdir "$HOME" -it kali-podman zsh -l
```

Cada comando `exec` abre una terminal dentro del contenedor correspondiente. Escribe `exit` para salir de esa terminal; el contenedor permanece encendido. Puedes abrir varias terminales del mismo entorno.

Si seguiste el ejemplo manual del apartado 1.1, entra con su variable:

```bash
podman exec --user "$(id -u):$(id -g)" --workdir "$HOME" -it "$contenedor" zsh -l
```

Los lanzadores equivalentes inician el contenedor si hace falta y renuevan la autorización gráfica:

```bash
dev-podman
parrotos-podman
kali-podman
```

## 4. Ver todos los entornos y servicios

```bash
# Todos los contenedores: dev, Parrot, Kali y cualquier servicio adicional.
podman ps -a

# Solo los que están funcionando.
podman ps

# Consumo de los contenedores activos, sin dejar un monitor abierto.
podman stats --no-stream

# Pods, volúmenes, redes e imágenes del motor del usuario.
podman pod ps
podman volume ls
podman network ls
podman images

# Sockets del usuario para Podman y la conexión Docker del dev.
systemctl --user status podman.socket workbench-podman.socket

# Proyectos de Docker Compose, incluidos los detenidos.
docker compose ls --all

# Contenedores pertenecientes a proyectos de Docker Compose.
podman ps -a --filter label=com.docker.compose.project

# Procesos de cada entorno.
podman top dev-podman
podman top parrotos-podman
podman top kali-podman

# Configuración de los tres.
podman inspect dev-podman parrotos-podman kali-podman
```

`podman ps -a` incluye también los contenedores anteriores y las copias de migración que conserves. `podman pod ps` muestra grupos de contenedores; puede estar vacío aunque existan contenedores individuales. El comando `docker` del host usa el cliente instalado en dev; si dev ya no existe, sigue administrando los servicios restantes con Podman directo.

## 5. Ejecutar programas y abrir aplicaciones

Una vez dentro de cualquiera de los tres entornos, puedes trabajar sobre tus documentos del host:

```bash
cd ~/Documents/Programacion
nvim .
```

Desde el host también puedes ejecutar un programa sin abrir otra shell:

```bash
podman exec --user "$(id -u):$(id -g)" dev-podman nvim --version
podman exec --user "$(id -u):$(id -g)" parrotos-podman nvim --version
podman exec --user "$(id -u):$(id -g)" kali-podman nvim --version
```

Para las aplicaciones gráficas de tus perfiles se necesita una autorización de pantalla vigente. Después de iniciar el contenedor, puedes actualizarla con Podman directo; el ejemplo usa dev, pero puedes sustituir su nombre por Parrot o Kali:

```bash
podman exec --user "$(id -u):$(id -g)" -i dev-podman \
    sh -c 'umask 077; cat > "$HOME/.Xauthority"' < "${XAUTHORITY:-$HOME/.Xauthority}"

podman exec --user "$(id -u):$(id -g)" \
    --env DISPLAY="$DISPLAY" --env XAUTHORITY="$HOME/.Xauthority" \
    dev-podman presentacion iniciar
```

`presentacion` y Hermes están instalados solo en dev. En Parrot y Kali ejecuta el programa gráfico que hayas instalado allí. Estos comandos aprovechan los montajes gráficos establecidos al crear cada perfil; el ejemplo básico `dev-ejemplo` no los incluye.

Al crear el contenedor se conectan los sockets disponibles de X11/Wayland y audio; `dev` recibe KVM cuando existe y los perfiles reciben `/dev/dri` cuando está disponible. X11 comparte solamente el socket del display padre y conserva un directorio privado para Xephyr. La autorización se copia al home interno y se renueva al entrar, sin depender de un archivo temporal del host montado permanentemente. No se usa `xhost` ni modo privilegiado. La conexión gráfica requiere una sesión gráfica y una autorización válidas.

En `dev` se comparte el bus de sesión en `/host-session/bus` para la integración con Awesome. La copia de `presentacion` lanza su terminal privada directamente dentro del nuevo contenedor y sus atajos invocan `podman exec dev-podman`, con comprobación del proceso dentro de su propio espacio de PIDs. Al salir de Hermes restaura los atajos. Los scripts originales de Distrobox no se modifican. Las fuentes del escritorio también se instalan dentro de `dev`.

```bash
dev-podman exec -- rider
dev-podman exec -- dbeaver
dev-podman exec -- flutter-emulator
# O desde una sesión de dev-podman:
presentacion iniciar
presentacion hermes
```

Abre tus proyectos usando `/host-home/...`; el home interno conserva espacio separado para herramientas y ajustes.

### Servicios de red y Docker/Compose

Dev usa el modo rootless predeterminado de Podman: accede al host mediante `host.containers.internal` y su `localhost` es interno. Parrot y Kali usan `--network host`, por lo que comparten las interfaces, rutas VPN y `localhost` del host. Las bases de datos ejecutadas en otros contenedores permanecen separadas y no se duplican automáticamente.

Docker, Compose y LazyDocker de `dev` usan el Podman rootless existente del host. `dev-podman integrate` configura un socket local de systemd que reenvía al socket existente, sin instalar paquetes en el host ni recrear contenedores. Los dos archivos de unidad quedan en `~/.config/systemd/user/workbench-podman.*`, y la conexión en `~/.local/state/podman-workbench/docker.sock`, accesible desde `/host-home`. Es el mismo motor y permite administrar también los contenedores anteriores: no constituye una separación de permisos.

Los servicios creados con Compose y sus volúmenes pertenecen al motor del host; borrar `dev-podman` no los elimina. Usa nombres de proyecto propios, por ejemplo `docker compose -p dev-podman-miapp up -d`; cuando autorices borrar esos datos, `docker compose -p dev-podman-miapp down --volumes` elimina los recursos de ese proyecto. Los bind mounts se resuelven en el host: usa la ruta real `/home/USUARIO/...` del host en la configuración de volúmenes, aunque edites el proyecto desde `/host-home/...`. Un archivo que existe solamente en el home interno no puede montarse mediante el motor del host.

## 6. Detener y reiniciar

Detener conserva programas, configuraciones y datos internos, pero cierra los procesos y aplicaciones del contenedor.

```bash
# Detener los tres entornos personales.
podman stop dev-podman parrotos-podman kali-podman

# Volver a iniciarlos.
podman start dev-podman parrotos-podman kali-podman

# Reiniciar uno en concreto.
podman restart dev-podman
podman restart parrotos-podman
podman restart kali-podman
```

Puedes indicar un solo nombre en `start` o `stop`. Los servicios adicionales de Docker/Compose aparecen en `podman ps -a` y se detienen indicando sus propios nombres, o desde la carpeta del proyecto con `docker compose stop`.

## 7. Borrar y entender qué permanece

Borrar elimina los programas y el home interno del contenedor elegido. Si creaste un ejemplo manual en el apartado 1.1, puedes retirarlo usando su variable, desde aquella misma terminal del host:

```bash
podman stop "$contenedor"
podman rm "$contenedor"
```

Para retirar uno de tus entornos reales, elige solamente el bloque correspondiente:

```bash
# Eliminar dev y sus volúmenes anónimos, si tuviera.
podman stop dev-podman
podman rm --volumes dev-podman
```

```bash
# Eliminar Parrot.
podman stop parrotos-podman
podman rm --volumes parrotos-podman
```

```bash
# Eliminar Kali.
podman stop kali-podman
podman rm --volumes kali-podman
```

El home real en `/host-home` y `Documents` enlazado permanecen. Las imágenes y los servicios creados mediante Docker/Compose tienen su propio ciclo de vida. Mientras dev siga disponible, desde la carpeta de un proyecto puedes ejecutar `docker compose down --volumes` para eliminar sus servicios y sus volúmenes de datos. Si también vas a borrar dev, haz esa limpieza de Compose antes; después puedes gestionar lo que permanezca mediante los comandos nativos de Podman.

## 8. Reconstruir y respaldar

Para reconstruir un entorno eliminado, vuelve a los comandos de recetas del apartado 1.2. No necesitas el antiguo Distrobox dev. `setup` conserva el home de cualquier contenedor que ya esté preparado; no sirve para recuperar datos borrados sin respaldo.

Una receta no reconstruye sesiones, bases de datos ni datos del teléfono virtual eliminados sin respaldo. Para conservarlos, respalda el home interno y `/opt` por separado. Usa GNU tar con `--sparse` para los discos de Android: un `podman commit` de esos discos puede expandir sus espacios vacíos y agotar el directorio temporal. Los respaldos e imágenes pueden contener credenciales y datos personales; son archivos privados, no imágenes para publicar.

## 9. Acciones con tus comandos de acceso

Los tres comandos permiten administrar su propio contenedor. Sin argumentos equivalen a `enter`:

| Acción | Dev | Parrot | Kali |
| --- | --- | --- | --- |
| Crear desde las recetas | `dev-podman setup --fresh` | `parrotos-podman setup` | `kali-podman setup` |
| Aplicar preferencias | `dev-podman integrate` | `parrotos-podman integrate` | `kali-podman integrate` |
| Entrar | `dev-podman enter` | `parrotos-podman enter` | `kali-podman enter` |
| Iniciar | `dev-podman start` | `parrotos-podman start` | `kali-podman start` |
| Ver estado | `dev-podman ps` | `parrotos-podman ps` | `kali-podman ps` |
| Ver configuración | `dev-podman inspect` | `parrotos-podman inspect` | `kali-podman inspect` |
| Ver registros | `dev-podman logs` | `parrotos-podman logs` | `kali-podman logs` |
| Detener | `dev-podman stop` | `parrotos-podman stop` | `kali-podman stop` |
| Reiniciar | `dev-podman restart` | `parrotos-podman restart` | `kali-podman restart` |
| Borrar el contenedor detenido | `dev-podman rm` | `parrotos-podman rm` | `kali-podman rm` |

Por ejemplo, `parrotos-podman exec -- nvim --version` ejecuta Neovim en Parrot sin abrir otra shell. Los comandos `enter`, `exec`, `setup`, `integrate` y `verify` usan las recetas de este repositorio; los pasos anteriores también muestran sus equivalentes nativos de Podman cuando corresponde.

`rm` conserva el comportamiento de Podman: si el contenedor está funcionando, primero debes detenerlo. Puedes indicar `rm --force` para borrarlo estando activo, y `rm --volumes` para eliminar también sus volúmenes anónimos. Se borra únicamente el contenedor del comando elegido; no se aceptan `--all`, `--latest` ni nombres de otros contenedores. Los documentos del host y los servicios de Compose permanecen.

## Cliente remoto de Podman

El lanzador usa `podman` por defecto. Para un cliente remoto explícito admite `PODMAN_WORKBENCH_CLIENT`, por ejemplo `podman --remote --url unix:///run/user/1000/podman/podman.sock`. Solo debe apuntar al motor rootless del usuario que comparte este home. No cambia automáticamente de motor ni usa sudo.

## Verificación de las recetas

```bash
python3 -B tests/workbench/test_podman_workbench.py
bash -n environments/workbench/podman/{prepare,finish,verify}.sh
```

Parrot Echo ofrece Neovim 0.10 y Tree-sitter 0.22 en sus repositorios. El bootstrap incorpora Neovim oficial 0.12.6 verificado por SHA-256, Tree-sitter CLI 0.27.1 y Yazi 26.9.1 cuando los paquetes disponibles no cumplen los requisitos. Estas versiones están registradas en `finish.sh`; los repositorios de APT no se mezclan.

## Copias de migración

El Distrobox `dev`, sus volúmenes anónimos y la copia temporal `dev-podman-migracion` se retiraron después de verificar las copias internas y arrancar Android sin los SDKs del host. También se eliminaron los SDKs, AVDs, cachés y datos de desarrollo correspondientes del home real. Las preferencias antiguas de Rider que diferían y un respaldo de la base de sesiones de Hermes se conservaron dentro del nuevo dev, en `~/.local/state/podman-workbench/retired-dev`.

Se conservan apagadas las copias de seguridad `parrotos-podman-migracion` y `kali-podman-migracion`; los entornos de seguridad anteriores permanecen sin borrar. Las imágenes compartidas que usa el dev nuevo se conservan.

Los lanzadores del host utilizan `dotfiles-dev-exec` para entrar al nuevo entorno y mapear el directorio actual a `/host-home`. Los instaladores opcionales se dirigen al dev nuevo; el manifiesto Distrobox ya no contiene un perfil dev.
