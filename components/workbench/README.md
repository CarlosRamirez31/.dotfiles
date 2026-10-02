# Workbench

Este componente prepara laboratorios Kali Linux y Parrot Security sobre Podman. Las imágenes incluyen la misma experiencia de terminal del host —Zsh, Oh My Zsh, Starship, Fastfetch, Eza, Bat, FZF, Zoxide y Vivid— y una copia completa de la configuración de Neovim con sus plugins y parsers.

Los laboratorios no usan Distrobox y no montan automáticamente `$HOME`, proyectos, llaves SSH ni dispositivos. Los paquetes y archivos creados dentro de cada contenedor permanecen en su filesystem hasta eliminarlo. Las dos imágenes comparten la red de la VM Arch mediante `--network host`, por lo que ven las interfaces y rutas de una VPN iniciada en Arch.

## Instalación y construcción

```bash
./install.sh workbench
labbox build kali
labbox build parrot
# o ambas, una después de la otra
labbox build all
```

La construcción usa las imágenes oficiales `kalilinux/kali-rolling` y `parrotsec/security`. Puede tardar y ocupar varios gigabytes: instala la interfaz de terminal, el entorno de compilación requerido por Neovim, LazyVim y herramientas de seguridad. Kali recibe explícitamente Nmap, Ffuf, Gobuster, Feroxbuster, SQLmap, Nikto, WhatWeb, Hydra, John, Hashcat, Metasploit, ExploitDB, clientes SMB, SecLists y wordlists. La imagen Security de Parrot ya trae su colección de seguridad; el build añade y normaliza las herramientas de terminal y Neovim.

Las imágenes construidas se llaman:

```text
localhost/dotfiles-kali:latest
localhost/dotfiles-parrot:latest
```

Se almacenan en el espacio rootful de Podman porque los laboratorios necesitan sockets RAW de red. Por eso `labbox` solicita `sudo` y una consulta manual equivalente se hace con `sudo podman images`, no con `podman images`.

Si la imagen oficial ya existe en el almacenamiento rootless —por ejemplo, por un contenedor Distrobox anterior— `labbox build` la transfiere al almacenamiento rootful antes de construir. Así evita descargar nuevamente la base de Parrot, que es especialmente grande; no detiene ni elimina el contenedor anterior.

## Sesiones desechables

```bash
labbox run kali
labbox run parrot
```

`run` genera un nombre único y usa `--rm`: al salir de Zsh se elimina esa instancia y todos sus cambios. La imagen base permanece disponible para iniciar otra sin reinstalar los programas.

Es posible abrir varias simultáneamente:

```bash
# Terminal 1
labbox run kali kali-uno

# Terminal 2
labbox run kali kali-dos
```

Sus archivos son independientes, pero ambas comparten la red de Arch. Dos procesos no pueden escuchar simultáneamente en el mismo puerto porque `--network host` no crea direcciones o puertos separados.

## Laboratorios persistentes

```bash
labbox create kali kali-principal
# salir con exit; los cambios permanecen

labbox enter kali-principal
labbox stop kali-principal
labbox rm kali-principal
labbox list
```

`create` conserva paquetes, usuarios, grupos, configuraciones y archivos internos entre sesiones. `rm` elimina solamente el contenedor indicado; no elimina la imagen reutilizable.

No hay volúmenes del host configurados. Para intercambiar un archivo deliberadamente se puede usar Podman:

```bash
sudo podman cp ./archivo kali-principal:/root/
sudo podman cp kali-principal:/root/resultado ./resultado
```

## VPN y privilegios

Conecta la VPN dentro de Arch antes de abrir el laboratorio:

```bash
vpn-on /ruta/laboratorio.ovpn
labbox run kali
```

Dentro del contenedor, `ip address` e `ip route` muestran la red de la VM y su interfaz `tun*` o `wg*`. Como el namespace de red es el mismo, una reconexión modifica las rutas visibles en los contenedores ya abiertos; si únicamente falla la resolución DNS, reinicia esa sesión.

`labbox` añade `NET_RAW` para Nmap, pero no añade `NET_ADMIN` ni usa `--privileged`. Esto permite paquetes RAW sin autorizar por defecto cambios en rutas, interfaces o firewall. El modo host sí permite alcanzar servicios que Arch exponga solamente en `127.0.0.1`; una herramienta no confiable debe ejecutarse en una VM separada, no en este laboratorio.

## Archivos administrados

| Archivo | Función |
| --- | --- |
| `Containerfile` | Construcción común sobre Kali o Parrot. |
| `container/install.sh` | Paquetes de terminal, desarrollo y seguridad. |
| `.local/bin/labbox` | Construcción y ciclo de vida seguro de las instancias. |
| `containerignore` | Evita enviar metadatos Git al contexto de construcción. |

## Diagnóstico

```bash
labbox --help
labbox list
sudo podman images
sudo podman system df
sudo podman inspect kali-principal
```

El componente nunca elimina contenedores, imágenes ni volúmenes automáticamente. Revisa siempre los nombres antes de usar `labbox rm` o cualquier comando de limpieza de Podman.
