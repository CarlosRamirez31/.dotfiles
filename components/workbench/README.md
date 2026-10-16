# Workbench

Este componente instala Podman rootless y Distrobox para mantener compiladores, dependencias de proyectos y herramientas de laboratorio fuera del Arch principal. Las definiciones viven en `~/.config/distrobox/distrobox.ini`; así los contenedores se pueden borrar y reconstruir sin recordar una instalación manual.

## Qué instala en el host

Instala `podman`, `distrobox` y selecciona `crun` explícitamente como runtime OCI. Habilita `podman.socket` como servicio del usuario. No usa Docker ni su daemon: Distrobox administra contenedores OCI mediante Podman rootless, sin ejecutar el motor como root.

Rootless necesita rangos asignados al usuario en `/etc/subuid` y `/etc/subgid`. El instalador los comprueba y avisa si faltan; después de corregirlos puede ser necesario cerrar la sesión del escritorio y volver a entrar.

## Perfiles declarados

| Nombre | Imagen oficial | Para qué se usa |
| --- | --- | --- |
| `dev` | `docker.io/library/archlinux:latest` | Desarrollo general con compiladores, Git, Neovim, Node.js y Python. |
| `kalilinux` | `docker.io/kalilinux/kali-rolling:latest` | Kali Linux con una selección práctica de herramientas para laboratorios autorizados. |
| `parrotos` | `docker.io/parrotsec/security:latest` | Parrot Security; su imagen ya incluye la colección CLI de herramientas de seguridad de Parrot. |

`kalilinux` y `parrotos` son los nombres locales elegidos para los contenedores. No son comandos especiales ni nombres impuestos por Distrobox. Las distribuciones se llaman Kali Linux y ParrotOS, y las imágenes de la tabla son las publicadas por sus proyectos.

Distrobox comparte con el contenedor el home, la sesión gráfica, dispositivos y varias rutas del host. Esto permite reutilizar los dotfiles, proyectos, llaves SSH y portapapeles, pero significa que el contenedor no es una frontera de seguridad para tus archivos personales. Aísla paquetes y dependencias; no debe usarse para ejecutar software deliberadamente hostil.

## Crear o reconstruir un contenedor

Después de `./install.sh workbench`, crea solamente el perfil que necesites:

```bash
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name kalilinux
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name parrotos
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name dev
```

Cada comando descarga la imagen, crea el contenedor, instala los paquetes declarados y prepara Neovim. Es idempotente: con `replace=false`, volver a ejecutarlo no elimina ni reemplaza un contenedor existente. Parrot Security es una descarga grande porque su imagen trae muchas herramientas.

No se necesita el antiguo wrapper `dotfiles-box`. Se usan directamente los comandos estándar de Distrobox, por lo que cualquier documentación o tutorial de Distrobox sigue siendo aplicable.

## Uso diario

```bash
distrobox enter kalilinux   # abrir otra terminal dentro del mismo Kali
distrobox enter parrotos    # entrar a ParrotOS
distrobox enter dev         # entrar al entorno de desarrollo
distrobox list              # ver contenedores y estado
distrobox stop kalilinux    # detenerlo; no borra paquetes ni archivos
exit                        # salir de la sesión actual
```

Puedes ejecutar `distrobox enter kalilinux` o `distrobox enter parrotos` en varias terminales a la vez. Todas entran al mismo contenedor correspondiente y comparten sus paquetes y procesos, pero cada terminal conserva su shell independiente.

Para borrar un contenedor hay que pedirlo explícitamente:

```bash
distrobox stop parrotos
distrobox rm parrotos
```

Esto elimina los paquetes instalados dentro de ese contenedor. Los proyectos y dotfiles del home compartido permanecen en el host. Antes de confirmar, revisa siempre que el nombre sea correcto.

## Qué prepara cada entorno de seguridad

Ambos reciben Zsh, Starship, Fastfetch, eza, FZF, Zoxide, Vivid, Bat y los plugins de sugerencias y resaltado. También reciben Git, utilidades de descarga y compresión, compiladores, Node.js, Python, Neovim, Tree-sitter, portapapeles X11, `jq` y Lazygit. El bootstrap sincroniza LazyVim y sus parsers desde una copia temporal de la configuración para no modificar el repositorio.

Kali añade una base deliberadamente limitada: Nmap, Ffuf, Gobuster, Feroxbuster, SQLmap, Nikto, WhatWeb, Netcat, Socat, DNS/Whois, clientes SMB, Enum4linux-ng, SecLists y Wordlists. No instala automáticamente todos los metapaquetes de Kali ni herramientas muy pesadas; se agregan cuando el laboratorio realmente las requiera.

Parrot usa `parrotsec/security`, que ya contiene los metapaquetes CLI de seguridad mantenidos por Parrot. Por eso no repetimos en el manifiesto una lista enorme de herramientas y evitamos mantener dos inventarios divergentes.

## Instalación de herramientas adicionales

Los paquetes se instalan dentro del contenedor, no en Arch:

```bash
distrobox enter kalilinux
sudo apt update
sudo apt install nombre-del-paquete
```

En ParrotOS se usa el mismo flujo con `apt`. En `dev`, que está basado en Arch, se usa `sudo pacman -S nombre-del-paquete`. Los binarios quedan disponibles en todas las terminales que entren al mismo contenedor. Si una herramienta debe formar parte reproducible del entorno, añádela a `additional_packages` en `distrobox.ini` en vez de dejarla solamente como instalación manual.

## Compatibilidad de `/tmp`

Kali y Parrot ejecutan un hook previo que enmascara dentro del contenedor las reglas `tmp.conf` y `x11.conf` de `systemd-tmpfiles`. Distrobox comparte `/tmp` con el host y una instalación rootless no puede cambiar su propietario; Arch ya administra esa ruta. Sin el hook, la primera entrada puede fallar con `fchownat() of /tmp failed` y dejar `dpkg` con código 100. El ajuste no cambia permisos del `/tmp` del host ni desactiva systemd.

## VPN

La VPN se inicia en el host con `vpn-on ruta/al/archivo.ovpn`, no dentro del contenedor. Al modificar la red del host, las sesiones de Distrobox usan esa conectividad. Se desconecta con `vpn-off`. Si un laboratorio exige capacidades de red especiales, comprueba primero sus instrucciones: Distrobox rootless comparte la red del host de forma distinta a una máquina virtual.

## Estado y diagnóstico

```bash
./install.sh workbench
systemctl --user status podman.socket
podman info
podman ps -a
podman system df
distrobox list
grep "^$(id -un):" /etc/subuid /etc/subgid
```

El componente nunca ejecuta podas automáticas. Para recuperar espacio, identifica primero las imágenes sin uso con `podman system df`; no borres imágenes o contenedores sin confirmar qué perfil depende de ellas.
