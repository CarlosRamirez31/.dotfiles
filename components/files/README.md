# Files

Este componente convierte el escritorio mínimo en un entorno capaz de navegar archivos, montar medios y abrir formatos comunes. Yazi aporta navegación tipo Neovim y funciona como selector de archivos del sistema; Thunar permanece como respaldo gráfico. Las asociaciones MIME permiten que Rofi, Firefox y aplicaciones GTK elijan programas predecibles.

## Paquetes y responsabilidades

| Paquete | Función |
| --- | --- |
| `yazi` | Gestor de terminal con previsualizaciones y navegación `h/j/k/l`. |
| `xdg-desktop-portal-termfilechooser` | Presenta Yazi al navegador y aplicaciones compatibles como selector del sistema. |
| `thunar`, `thunar-volman` | Gestor de archivos y reacción a medios removibles. |
| `tumbler` | Miniaturas en Thunar. |
| `gvfs`, `gvfs-mtp`, `gvfs-gphoto2`, `gvfs-smb` | Papelera, teléfonos, cámaras y recursos SMB. |
| `udisks2` | Montaje de discos por sesión sin ejecutar Thunar como root. |
| `file-roller` | Crear/extraer ZIP, 7z, RAR y tar. |
| `imv` | Visor de imágenes. |
| `mpv` | Audio y vídeo. |
| `zathura`, `zathura-pdf-mupdf` | PDF y backend MuPDF. |
| `tesseract-data-eng`, `tesseract-data-spa` | OCR inglés/español requerido por MuPDF. |
| `xdg-user-dirs` | Resuelve Documents, Downloads, Pictures y Videos según idioma. |

## Uso

```bash
./install.sh files
yazi
xdg-open documento.pdf
xdg-open imagen.png
gio mount smb://servidor/recurso
```

`Alt+E` abre Yazi en Alacritty y `Ctrl+Alt+E` abre Thunar. En Yazi se navega
con `h/j/k/l`, `Enter` entra en directorios, `Shift+Enter` abre el archivo en
su aplicación, `Space` selecciona y `q` sale. `gd`, `gp` y `gh`
saltan a Descargas, Imágenes y el directorio personal. Los volúmenes aparecen
en la barra lateral de Thunar y se montan mediante UDisks/GVfs; no hace falta
`sudo mount` para el uso normal.

Firefox y las aplicaciones que respetan XDG Desktop Portal abren Yazi al subir,
abrir o guardar archivos. `Shift+Enter` confirma el archivo señalado, `Space`
permite una selección múltiple y `Q` cancela el diálogo. Al guardar una descarga,
`r` abre el nombre sugerido; al escribir el nombre y pulsar `Enter`, el cambio de
nombre y la selección quedan confirmados en un solo paso. Para elegir el destino
de cada descarga, activa «Preguntar siempre dónde guardar los archivos» en el
navegador.

## Asociaciones predeterminadas

| Contenido | Aplicación |
| --- | --- |
| Directorios | Thunar |
| HTTP, HTTPS y HTML | Firefox |
| PDF | Zathura |
| BMP, GIF, JPEG, PNG, SVG y WebP | imv |
| FLAC, MP3, Ogg y vídeos comunes | mpv |
| ZIP, 7z, RAR y tar | File Roller |

Se declaran en `.config/mimeapps.list`. Firefox viene de `desktop-extras`; si ese componente no está instalado, la asociación queda preparada pero no podrá abrirse hasta instalarlo.

En imv, `Shift++` amplía la imagen y `Shift+-` la reduce. Este último atajo se
declara de forma explícita porque esa combinación produce el carácter `_`, que
imv no enlaza de fábrica.

MPV conserva la selección automática de GPU en hardware físico. En VMware,
donde la sesión exporta `LIBGL_ALWAYS_SOFTWARE=1`, el perfil
`software-renderer` usa la salida `wlshm`, creada para escalado por software en
Wayland. Esto evita que MPV 0.41 intente Vulkan sin driver, aborte durante su
fallback hacia X11 o pierda cuadros renderizando OpenGL mediante `llvmpipe`.

## Efectos del instalador y diagnóstico

Además de enlazar `mimeapps.list`, configura el portal `FileChooser` para Yazi,
conserva los demás portales de Hyprland/GTK y ejecuta `xdg-user-dirs-update`, que
crea o actualiza nombres de carpetas XDG del usuario.

```bash
xdg-mime query default inode/directory
xdg-mime query default application/pdf
systemctl --user status xdg-desktop-portal-termfilechooser.service
journalctl --user -eu xdg-desktop-portal-termfilechooser.service
gio mount -l
systemctl status udisks2.service
```

Si un teléfono no aparece, desbloquéalo y selecciona MTP. Si faltan miniaturas, reinicia Thunar con `thunar -q` y ábrelo otra vez. No ejecutes Thunar como root: rompería permisos y el contexto de la sesión.
