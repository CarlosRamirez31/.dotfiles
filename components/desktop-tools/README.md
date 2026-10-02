# Desktop tools

Implementa capturas e historial local del portapapeles para Wayland. Grim captura, Slurp selecciona geometría, Swappy anota, wl-clipboard integra el portapapeles y Cliphist conserva entradas.

## Dependencias

| Paquete | Función |
| --- | --- |
| `grim` | Captura una salida o región en PNG. |
| `slurp` | Selecciona una región. |
| `swappy` | Anota, recorta y confirma. |
| `wl-clipboard` | Proporciona `wl-copy` y `wl-paste`. |
| `cliphist` | Almacena y decodifica texto e imágenes. |

## Capturas

```bash
screenshot full
screenshot area
screenshot edit
```

Se guardan con fecha/hora en `$(xdg-user-dir PICTURES)/Screenshots` y se copian como `image/png`. `edit` usa un temporal y solo conserva el resultado confirmado por Swappy.

| Atajo | Acción |
| --- | --- |
| `Print` | Pantalla completa. |
| `Alt+Print` | Región. |
| `Alt+Shift+S` | Región y editor. |

## Portapapeles

```bash
clip
clip-clear
cliphist list
```

`Super+C` o `Alt+C` abre Rofi. Enter restaura la entrada elegida y la pega en
la ventana que tenía el foco; en terminales utiliza `Ctrl+Shift+V`. La limpieza
exige elegir “Sí”; no existe borrado silencioso. Dos servicios observan texto e
imágenes, reinician tras fallos y viven con `graphical-session.target`.

## Instalación, servicios y archivos

```bash
./install.sh desktop-tools
systemctl --user status dotfiles-cliphist-text.service
systemctl --user status dotfiles-cliphist-image.service
```

El instalador enlaza `dotfiles-screenshot`, `dotfiles-clipboard`, `dotfiles-clipboard-clear` y dos unidades systemd. Las habilita siempre y solo las reinicia en el acto si detecta Wayland.

```bash
journalctl --user -u dotfiles-cliphist-text.service -u dotfiles-cliphist-image.service
echo texto-de-prueba | wl-copy
cliphist list
```

Si no aparece la prueba, verifica ambos servicios y que `WAYLAND_DISPLAY` pertenezca a la sesión UWSM.
