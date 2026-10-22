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
