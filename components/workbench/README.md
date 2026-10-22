# Workbench

El entorno de desarrollo activo es **dev-podman**, con home interno y acceso al home real en `/host-home`. Las recetas, reconstrucción, gráficos, Docker y límites de persistencia se documentan en [podman/README.md](podman/README.md).

```bash
dev-podman
parrotos-podman
kali-podman
dotfiles-podman verify all
```

También puedes indicar la acción después del nombre:

| Acción | Dev | Parrot | Kali |
| --- | --- | --- | --- |
| Entrar | `dev-podman enter` | `parrotos-podman enter` | `kali-podman enter` |
| Iniciar | `dev-podman start` | `parrotos-podman start` | `kali-podman start` |
| Ver estado | `dev-podman ps` | `parrotos-podman ps` | `kali-podman ps` |
| Detener | `dev-podman stop` | `parrotos-podman stop` | `kali-podman stop` |
| Reiniciar | `dev-podman restart` | `parrotos-podman restart` | `kali-podman restart` |
| Borrar el contenedor detenido | `dev-podman rm` | `parrotos-podman rm` | `kali-podman rm` |

`rm --force` permite borrarlo estando activo y `rm --volumes` retira sus volúmenes anónimos. Cada comando actúa únicamente sobre su propio contenedor. Las acciones `inspect`, `logs`, `exec`, `setup`, `integrate` y `verify` se detallan en la guía de Podman.

El antiguo Distrobox `dev` se retiró tras verificar la migración. Los lanzadores del host `rider`, `dbeaver`, `docker`, `flutter-emulator`, `lazydocker`, `hermes` y `presentacion` utilizan el nuevo contenedor. Conservan el directorio del proyecto mediante `/host-home`. Rider también traduce rutas absolutas del home; los argumentos de volúmenes de Docker se conservan como rutas del host.

Los componentes opcionales `./install.sh rider dbeaver docker flutter hermes` instalan sus programas dentro del `dev-podman` existente. No crean un Distrobox ni instalan paquetes en el host. Para reconstruir un dev eliminado se utiliza `dev-podman setup --fresh`.

## Archivos y eliminación

Los SDKs de Flutter/Android, AVDs, Gradle, Pub, .NET de usuario y datos de Rider están dentro del nuevo contenedor. Los proyectos y documentos en `/host-home` permanecen al eliminarlo. El escritorio del host, sus dotfiles, Neovim, fuentes, fondos y credenciales personales se conservan.

Docker/Compose utilizan el Podman rootless del host. Los servicios, redes y volúmenes creados allí tienen su propio ciclo de vida; borrar dev no los borra automáticamente. Usa un nombre de proyecto de Compose distinto para cada aplicación.

## Distrobox de seguridad anteriores

El manifiesto `~/.config/distrobox/distrobox.ini` conserva los perfiles anteriores `kalilinux` y `parrotos`. La retirada de dev no los elimina ni modifica sus contenedores. Los perfiles nuevos de uso diario son `kali-podman` y `parrotos-podman`.

```bash
distrobox enter kalilinux
distrobox enter parrotos
distrobox list
```

Los Distrobox anteriores comparten directamente el home del host. Los nuevos perfiles tienen home propio. No uses los anteriores para reinstalar SDKs de desarrollo en el home compartido.

## Instalación inicial del proveedor

`./install.sh workbench` es el instalador inicial del proveedor: instala Podman, crun, Distrobox y utilidades en el host, y habilita el socket rootless. No hace falta volver a ejecutarlo para utilizar o reconstruir los contenedores de una máquina que ya tiene esos componentes.
