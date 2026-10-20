# Hermes (opcional)

Este componente se instala **solo si lo pides por nombre**. No forma parte de `./install.sh`, `./install.sh all` ni del perfil normal de `dev`.

```bash
./install.sh hermes           # añadirlo a una instalación existente
./install.sh all hermes       # escritorio completo más Hermes
./install.sh --dry-run all    # ver la selección sin instalar nada
```

Requiere el componente `workbench` (Podman rootless y Distrobox). Si todavía no existe:

```bash
./install.sh workbench hermes
```

Crea el contenedor `dev` si falta; conserva uno existente. Dentro instala Hermes CLI, las skills personalizadas, el escritorio Awesome anidado con Xephyr, Polybar, Picom, Firefox, Alacritty y el puente de capturas. Los paquetes de presentación se instalan dentro de `dev`; este componente no añade paquetes al host. No usa una máquina virtual ni XFCE.

## Qué se reproduce

- `/opt/hermes/.hermes`: Hermes, configuración, skills y entorno Python académico dentro de dev.
- `/opt/presentacion`: escritorio redimensionable, barra sin «PRESENTACIÓN», wallpaper del host, fuentes, terminal y perfil de Firefox independiente.
- Skills propias: `academic-apa-writer` (APA 7 y perfil UNICARIBE), `humanize-global`, personalización de `youtube-content` y bundle `/academico`. Las skills de fábrica las mantiene Hermes.
- `~/Documents/Universidad/{entradas,salidas,muestras}`: documentos compartidos entre host y dev; `salidas/capturas` conserva los PNG. No se copian tus documentos personales al repositorio.
- Print y Alt+Shift+S del **host** se conectan temporalmente a Hermes solo durante `presentacion hermes`. Al cerrar Hermes, incluso abruptamente, se restauran los atajos anteriores. No se editan archivos de Awesome del host.
- Registro acotado de CPU/RAM/swap mientras se ejecuta la presentación, y comandos de cierre y eliminación.

No se versionan `.env`, autenticaciones, conversaciones, memoria personal, cookies, datos del navegador ni el respaldo original. El instalador combina los ajustes académicos con una configuración ya existente y conserva el proveedor y la autenticación. Los archivos administrados que cambian se respaldan dentro de `/opt/presentacion/backups`.

Las rutas personales se generan a partir del home real; no se fija un nombre de usuario. El fondo inicial se toma del estado del componente wallpaper o de sus fondos disponibles. Las preferencias visuales reutilizan tus archivos del host sin modificar los originales.

## Autenticación y uso

Conecta tu proveedor solo después de instalar, dentro de dev:

```bash
distrobox enter dev
hermes setup
presentacion iniciar
presentacion hermes
```

Hermes ocupa **la misma terminal exterior** desde la que abriste el escritorio virtual. Dentro del Firefox virtual se inicia la videoconferencia y se comparte su pantalla completa. Las ventanas privadas del host quedan fuera de esa captura de la reunión.

Con Hermes activo, los atajos del host envían imágenes de la pantalla física a Hermes:

- `Print`: todas las pantallas físicas.
- `Alt+Shift+S` o `Alt+Print`: región seleccionada.
- Si Xephyr capturó teclado/ratón, `Ctrl+Shift` los libera para usar los atajos del host.

Las capturas realizadas dentro del Awesome virtual se guardan normalmente y no se envían. No hay captura continua. Desde otra terminal de dev:

```bash
presentacion captura-host area
presentacion hermes-estado
presentacion hermes-detener
presentacion tamaño 1600x900
presentacion cpu
presentacion cerrar
```

Para terminar Hermes también puedes usar `/quit` o `/exit`. Ejecutar `hermes` sin el comando `presentacion hermes` no activa el puente. Al cerrar el escritorio virtual también termina ese Hermes. Los detalles de uso quedan en `/opt/presentacion/LEEME.md`.

## Instalación aislada y versión

Se usa el [instalador oficial de Hermes](https://hermes-agent.nousresearch.com/docs/getting-started/installation), fijado al commit probado de v0.22.2 para que la integración de adjuntos no cambie silenciosamente. Se ejecutan únicamente sus etapas headless y se publica el lanzador dentro del contenedor. Se omiten sus pasos de modificación del shell y publicación en el home compartido. No se descarga su navegador automatizado ni el controlador de computer-use. Tampoco se construye Hermes Desktop ni se inicia un gateway.

El wrapper del contenedor está en `/usr/local/bin/hermes`. Su configuración desactiva la publicación automática de lanzadores en el home compartido. Puedes actualizar con `hermes update`, pero una versión futura puede cambiar la API interna de adjuntos: comprueba el puente antes de usarlo.

Reinstalar con la sesión cerrada actualiza los archivos administrados sin borrar perfiles, documentos ni conversaciones. Si la presentación está activa, se detiene la instalación antes de modificarla y se indica cómo cerrarla.

## Eliminación

Dentro de dev:

```bash
presentacion desinstalar --confirmar
# Opcional: también los paquetes añadidos para la presentación
presentacion desinstalar --confirmar --paquetes
```

Esto conserva Hermes y Universidad. Eliminar el contenedor `dev` elimina toda su instalación interna de Hermes y presentación; **Universidad y los respaldos originales del host permanecen**. Exporta las conversaciones o credenciales que quieras conservar antes de borrar el contenedor. El componente nunca elimina el contenedor automáticamente.

## Comprobaciones sin instalar

```bash
./install.sh --dry-run
./install.sh --dry-run all hermes
python components/hermes/tests/test_optional.py
```

Las pruebas comprueban la exclusión por defecto, selección y orden explícitos, rechazo de opciones inválidas, renderizado con otro home que contiene espacios, conservación de ajustes del proveedor y ausencia de datos privados en el payload. No crean contenedores ni llaman a un modelo.
