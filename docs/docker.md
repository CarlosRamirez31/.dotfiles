# Docker opcional en dev

`./install.sh docker` o `./install.sh workbench docker` instala Docker CLI, Compose y Buildx únicamente dentro de `dev`. La instalación normal y `all` lo excluyen.

El entorno existente es `dev-podman`, un contenedor rootless con home interno. El cliente Docker se conecta a la API compatible de **Podman rootless del host**, que administra los contenedores del usuario. No se configura un daemon dockerd independiente dentro de este contenedor; Docker y Podman comparten contenedores e imágenes. Las características exclusivas de Docker Engine/BuildKit pueden no ser compatibles con este backend.

```bash
docker ps
docker compose version
docker compose up -d
lazydocker
```

`docker` funciona también desde el host y conserva el directorio actual. Se respetan `DOCKER_HOST`, `DOCKER_CONTEXT` y los contextos personalizados; el socket Podman solo se selecciona por defecto cuando no hay otro motor configurado. Los puertos publicados y las carpetas compartidas pertenecen al host.

## Fuentes del módulo

Instalador: [`setup/modules/docker/install.sh`](../setup/modules/docker/install.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
