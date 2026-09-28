# Wallpaper

Este componente instala Awww y un fondo versionado. Mantener imagen y comando juntos garantiza que una sesión nueva tenga fondo reproducible sin depender de rutas privadas o descargas externas.

## Funcionamiento

El archivo `.config/wallpapers/arch-bsod.png` se enlaza al home. Hyprland comprueba si `awww-daemon` está activo, lo inicia si hace falta y aplica la imagen sin transición. El instalador repite esa operación si detecta una sesión Hyprland activa; fuera de sesión queda preparada para el próximo login.

```bash
./install.sh wallpaper
awww img ~/.config/wallpapers/arch-bsod.png --transition-type none
awww query
```

El log del daemon iniciado por el instalador queda en `${XDG_RUNTIME_DIR:-/tmp}/awww-dotfiles.log`.

## Cambiar el fondo

Para que el cambio sea reproducible, añade/reemplaza el recurso dentro del componente y actualiza la ruta en `components/hyprland/dotfiles/.config/hypr/lua/core.lua`. Aplicar una imagen arbitraria con `awww img` solo cambia la sesión actual; en el próximo arranque vuelve la ruta administrada.

Awww acepta transiciones para cambios manuales:

```bash
awww img /ruta/imagen.jpg --transition-type grow --transition-duration 1
```

## Diagnóstico

```bash
pgrep -a awww-daemon
awww query
tail -f "${XDG_RUNTIME_DIR:-/tmp}/awww-dotfiles.log"
```

Si no aparece el fondo, verifica que se ejecuta dentro de Wayland, que el enlace de la imagen existe y que solo haya un daemon asociado a la sesión actual.
