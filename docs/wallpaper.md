# Wallpaper

Este componente instala Feh y un fondo versionado de respaldo para Awesome/X11.
Las imágenes personales viven en `~/Pictures/Wallpapers` y no se suben a Git.

## Uso

```bash
./install.sh wallpaper
dotfiles-wallpaper
dotfiles-wallpaper restore
```

`Alt+W` abre una galería Rofi oscura con cuatro columnas de miniaturas. Escribe
para filtrar, usa las flechas o el ratón para elegir, `Enter` aplica la imagen y
`Escape` cierra sin cambiar nada. ImageMagick genera las miniaturas en la caché
XDG y se reutilizan en las próximas aperturas.

Feh aplica el fondo y la ruta elegida se guarda en
`~/.local/state/dotfiles/wallpaper`. En cada inicio de Awesome se restaura la
última selección; si el archivo desapareció, usa la primera imagen disponible y
finalmente `.config/wallpapers/mocha-aurora.png`.

Se reconocen JPG, JPEG, PNG, WebP, GIF, BMP y AVIF colocados en
la carpeta o en cualquiera de sus subcarpetas. Para usar otra ubicación puntualmente:

```bash
export DOTFILES_WALLPAPER_DIR="$HOME/Imagenes/Fondos"
dotfiles-wallpaper
```

## Diagnóstico

```bash
command -v feh python
echo "$XDG_SESSION_TYPE"
test -r ~/.config/wallpapers/mocha-aurora.png
```

La sesión debe indicar `x11`. El fondo se aplica con Feh y el selector usa Rofi.

## Fuentes del módulo

Instalador: [`setup/modules/wallpaper.sh`](../setup/modules/wallpaper.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.

## Selector animado Bollow (X11)

Con la instalación opcional disponible, `dotfiles-wallpaper-picker` abre el
selector Quickshell. `dotfiles-wallpaper-sync` sincroniza la biblioteca de Steam
y muestra el progreso de miniaturas y animaciones; si el selector está abierto,
indica que debe cerrarse para continuar la generación.

El código de esta integración vive en tres repositorios. Versiones locales
compatibles guardadas el 2026-11-24:

- Dotfiles: lanzadores, servicios systemd, perfiles de energía y pausa Awesome.
- [qs-wallpaper-picker](https://github.com/CarlosRamirez31/qs-wallpaper-picker),
  en `~/Documents/Programacion/qs-wallpaper-picker`, commit `9308248`: selector,
  biblioteca independiente, previews y controlador X11.
- [linux-wallpaperengine](https://github.com/CarlosRamirez31/linux-wallpaperengine),
  en `~/Documents/Programacion/linux-wallpaperengine`, commit `fbb6741`: motor nativo,
  correcciones de escenas y aviso de primer fotograma.

Los dos últimos commits pertenecen a repositorios separados, no están incluidos
como código ni submódulos dentro de dotfiles. Para reinstalar hay que conservar
esos repositorios/versiones y preparar sus dependencias: runtime Quickshell local
(`~/.local/share/bollow-picker/runtime`), motor compilado en `build/output`, GLFW
local en `~/.local/share/bollow-picker/engine-deps/usr/lib`, xwinwrap, mpv, ffmpeg
(ffprobe), ImageMagick y feh. Los binarios y los fondos descargados no se guardan
como archivos de Git. Sin el selector instalado se conserva el selector Rofi.

La biblioteca independiente se guarda en `~/Pictures/Wallpapers/Steam`, con
proyectos completos y recursos del motor. El servicio `bollow-wallpaper-sync.path`
reacciona a cambios locales de Steam; no usa un temporizador periódico. Las bajas
explícitas se confirman al minuto y se conservan como recuperables en
`~/.local/share/bollow-picker/removed`. Una instalación ausente o una biblioteca
vacía no provoca borrado masivo de las copias.

Awesome pausa cada fondo por separado si las ventanas cubren el área útil de su
monitor (ignorando los márgenes del mosaico). El selector pausa todos los fondos;
al cerrarse solo reanuda los visibles. El controlador espera el primer fotograma
antes de pausar y valida identidad de procesos/grupos antes de señalarlos.
Las escenas pausan el render mediante un marcador por monitor y siguen atendiendo
eventos gráficos; no se suspenden con SIGSTOP, que provocaba bloqueos de X11 al
cambiar de escritorio o mostrar vistas previas. Los vídeos usan la pausa interna de MPV después del primer fotograma;
los fondos web esperan la primera pintura de CEF. Al cambiar de fondo se cierran
y recogen los grupos de procesos, incluso si CEF se movió a otro scope de systemd.
MPV usa OpenGL/EGL y VA-API del escritorio para evitar la selección automática
de NVIDIA/Vulkan en esta sesión híbrida.

Las escenas usan el proveedor gráfico del escritorio, sin forzar NVIDIA PRIME:
el offload en esta sesión híbrida presentó congelamientos de la salida externa.
En equilibrado/rendimiento el límite de FPS sigue los Hz activos; ahorro usa 30/15 FPS.
El render espera completar el trabajo de GPU de cada fotograma antes de iniciar
el siguiente para evitar acumular trabajo delante del compositor.
Cambiar un perfil con `dotfiles-power-profile` reinicia solo el reproductor activo.
El límite no garantiza la tasa de renderizado real. La compatibilidad de escenas
no es universal; las seis escenas 3D predeterminadas no compatibles siguen marcadas.

El módulo wallpaper enlaza los lanzadores y unidades y activa la escucha de
cambios si encuentra el repositorio del selector. Diagnóstico:

```bash
systemctl --user status bollow-wallpaper.service bollow-wallpaper-sync.path
journalctl --user -u bollow-wallpaper-sync.service -u bollow-wallpaper-previews.service
```

El [fork de xwinwrap](https://github.com/CarlosRamirez31/xwinwrap), local en
`~/Documents/Programacion/xwinwrap`, contiene una corrección:
`-ovr` respeta `-g` explícito en vez de expandirse a todo el escritorio X11.
Se compila con `make` y se instala en `~/.local/bin/xwinwrap`; cada ventana debe
medir lo mismo que su monitor y conservar el tipo de ventana DESKTOP.
