# Wallpaper

Este componente instala Awww, Waypaper y un fondo versionado de respaldo. Un
overlay GTK Layer Shell aporta el carrusel visual; Waypaper se limita a aplicar
y persistir la selección, mientras Awww dibuja el fondo. Las imágenes personales
se mantienen fuera de Git en `~/Pictures/Wallpapers`.

## Funcionamiento

Al iniciar Hyprland, `dotfiles-wallpaper restore` delega en Waypaper la
restauración de la última selección. Solamente aplica
`.config/wallpapers/arch-bsod.png` cuando la carpeta no existe o no contiene
imágenes compatibles.

```bash
./install.sh wallpaper
dotfiles-wallpaper
awww query
```

También se abre con `Alt+W`. El overlay tiene un fondo opaco, ocupa la mitad inferior
del monitor y muestra como máximo tres imágenes sobre aproximadamente el 94% del
ancho: anterior, selección ampliada en el centro y siguiente. Con dos archivos,
la alternativa se repite a ambos lados; con uno solo aparece la imagen central.
Los laterales comparten una línea inferior y la selección central queda elevada,
como si flotara sobre esa base, además de ser ligeramente más alta.
Las flechas izquierda/derecha o `H/L` recorren el carrusel, `Enter` aplica la
selección y `Escape` sale. Waypaper conserva la elección en su estado XDG para
la próxima sesión. El carrusel hace carga diferida fuera del hilo de la interfaz:
conserva la lista como rutas y solo mantiene en caché las tres imágenes visibles,
ya reducidas al tamaño de sus tarjetas. Los vecinos se preparan también al tamaño
central para que el siguiente movimiento sea inmediato. Las miniaturas persisten
en `~/.cache/dotfiles-wallpaper` y se invalidan si cambia el archivo, el tamaño de
la tarjeta o la resolución. Archivos corruptos o que solo aparenten ser imágenes
por su extensión se omiten.
Además, una segunda pulsación de `Alt+W` no crea otro overlay mientras el primero
siga abierto.

Se reconocen archivos JPG, JPEG, PNG, WebP, GIF, BMP y AVIF colocados
directamente en la carpeta. La configuración mutable vive en
`~/.config/waypaper/config.ini`; el instalador solo la crea cuando todavía no
existe. El tema de Waypaper administrado está en
`~/.config/waypaper/style.css`. Para abrir otra ubicación puntualmente:

```sh
export DOTFILES_WALLPAPER_DIR="$HOME/Imagenes/Fondos"
dotfiles-wallpaper
```

## Diagnóstico

```bash
pgrep -a awww-daemon
awww query
waypaper --list
tail -f "${XDG_RUNTIME_DIR:-/tmp}/awww-dotfiles.log"
```

Si no aparece el fondo, verifica que se ejecuta dentro de Wayland, que las
imágenes sean legibles y que solo haya un daemon asociado a la sesión actual.
