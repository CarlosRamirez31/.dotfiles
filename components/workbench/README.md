# Workbench

Este componente instala Podman rootless y Distrobox para mantener compiladores, dependencias de proyectos y herramientas de laboratorio fuera del Arch principal. La instalación no descarga imágenes ni crea contenedores; el espacio solo se consume al pedir un perfil.

## Paquetes y diseño

Instala `podman`, `distrobox` y selecciona `crun` explícitamente como runtime OCI. Así Pacman no pregunta entre proveedores. `crun` es ligero y apropiado para rootless; `krun` solo sería necesario para aislamiento KVM adicional.

Habilita `podman.socket` como servicio de usuario. Rootless requiere rangos en `/etc/subuid` y `/etc/subgid`; el instalador advierte si faltan y puede ser necesario cerrar sesión después de corregirlos.

## Perfiles

| Perfil | Nombre | Imagen | Uso previsto |
| --- | --- | --- | --- |
| `dev` | `dotfiles-dev` | `archlinux:latest` | Compiladores y dependencias de proyectos. |
| `pentest` | `dotfiles-pentest` | `kalilinux/kali-rolling:latest` | Laboratorios de seguridad autorizados. |

Distrobox integra home, terminal y aplicaciones del usuario; esa comodidad significa que un contenedor no es una frontera para archivos personales. Sirve para aislar paquetes, no secretos hostiles.

## Referencia de comandos

```bash
dotfiles-box create dev
dotfiles-box enter dev
dotfiles-box stop dev
dotfiles-box remove dev
dotfiles-box create pentest
dotfiles-box setup pentest
dotfiles-box enter pentest
dotfiles-box list
```

`create pentest` descarga Kali, completa su inicialización y ejecuta el setup
entero; al terminar el contenedor ya está listo. `setup pentest` es idempotente:
sirve para completar, reparar o actualizar un contenedor existente. `enter`
abre shell, `stop` detiene, `list` delega a Distrobox y `remove` solicita
confirmación `[y/N]` antes de borrar el contenedor y sus paquetes instalados.
Datos guardados directamente en el home compartido no se eliminan con el
contenedor.

Para el perfil Kali, `create` también enmascara dentro del contenedor las
reglas `tmp.conf` y `x11.conf` de `systemd-tmpfiles`. Distrobox comparte el
`/tmp` del host y una instalación rootless no puede cambiar su propietario;
Arch ya administra esas rutas compartidas. Sin esta compatibilidad, el primer
`enter` puede terminar con `fchownat() of /tmp failed` y código 100 de `dpkg`.
La corrección no desactiva systemd ni cambia permisos del `/tmp` de Arch.

El setup instala el entorno de terminal (Zsh, Starship, Fastfetch, eza, FZF,
Zoxide y plugins), Neovim con sus dependencias de compilación y plugins, y una
base de laboratorio: Nmap, Ffuf, Gobuster, Feroxbuster, SQLmap, Nikto,
WhatWeb, Netcat, Socat, utilidades DNS/Whois, clientes SMB, Enum4linux-ng,
SecLists y Wordlists. No instala metapaquetes Kali completos, Metasploit ni
herramientas de cracking pesadas; esas se agregan conscientemente cuando un
laboratorio las requiera.

## Dentro del contenedor

```bash
sudo pacman -S paquete       # perfil dev
sudo apt update              # perfil pentest
sudo apt install paquete
exit
```

## Estado y diagnóstico

```bash
./install.sh workbench
systemctl --user status podman.socket
podman info
podman ps -a
distrobox list
grep "^$(id -un):" /etc/subuid /etc/subgid
```

Si Podman informa que faltan rangos subordinados, configúralos mediante las herramientas del sistema y vuelve a iniciar sesión. Para liberar imágenes no usadas, revisa primero `podman system df`; el componente no ejecuta podas automáticas ni destructivas.
