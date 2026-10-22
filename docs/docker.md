# Docker opcional en dev

`./install.sh docker` o `./install.sh workbench docker` instala Docker CLI, Compose y Buildx únicamente dentro de `dev`. La instalación normal y `all` lo excluyen.

El `dev` existente es un Distrobox rootless con red integrada. El cliente Docker se conecta a la API compatible de **Podman rootless del host**, que ya administra Distrobox. No se configura un daemon dockerd independiente dentro de este contenedor; Docker y Podman comparten contenedores e imágenes. Las características exclusivas de Docker Engine/BuildKit pueden no ser compatibles con este backend.

```bash
docker ps
docker compose version
docker compose up -d
lazydocker
```

`docker` funciona también desde el host y conserva el directorio actual. Se respetan `DOCKER_HOST`, `DOCKER_CONTEXT` y los contextos personalizados; el socket Podman solo se selecciona por defecto cuando no hay otro motor configurado. Los puertos publicados y las carpetas compartidas pertenecen al host.
