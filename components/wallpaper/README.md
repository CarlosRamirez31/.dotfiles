# Wallpaper

Este componente instala Feh y un fondo versionado de respaldo para Awesome/X11.
Las imágenes personales viven en `~/Pictures/Wallpapers` y no se suben a Git.

## Uso

```bash
./install.sh wallpaper
dotfiles-wallpaper
dotfiles-wallpaper restore
```

`Alt+W` abre el carrusel GTK como ventana X11 normal. Muestra la selección
actual y sus vecinas con miniaturas cargadas fuera del hilo gráfico. Las flechas
izquierda/derecha o `H/L` recorren los fondos, `Enter` aplica la selección y
`Escape` sale. Una segunda pulsación no crea otra instancia.

Feh aplica el fondo y la ruta elegida se guarda en
`~/.local/state/dotfiles/wallpaper`. En cada inicio de Awesome se restaura la
última selección; si el archivo desapareció, usa la primera imagen disponible y
finalmente `.config/wallpapers/mocha-aurora.png`.

Se reconocen JPG, JPEG, PNG, WebP, GIF, BMP y AVIF colocados directamente en
la carpeta. Para usar otra ubicación puntualmente:

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

La sesión debe indicar `x11`. Este componente no ejecuta Awww, Waypaper ni GTK
Layer Shell.
