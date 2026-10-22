# Files

Este componente convierte el escritorio mínimo en un entorno capaz de navegar archivos, montar medios y abrir formatos comunes. Yazi aporta navegación de terminal tipo Neovim; el portal GTK ofrece el selector de archivos del sistema y Thunar permanece como gestor gráfico. Las asociaciones MIME permiten que Rofi, Firefox y aplicaciones GTK elijan programas predecibles.

## Paquetes y responsabilidades

| Paquete | Función |
| --- | --- |
| `yazi` | Gestor de terminal con previsualizaciones y navegación `h/j/k/l`. |
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

En la sesión Awesome, el portal de archivos usa GTK y X11. Firefox y las aplicaciones compatibles
abren ese selector al subir, abrir o guardar archivos. Yazi sigue disponible
como gestor de terminal (`Alt+E`); Thunar es el respaldo gráfico.

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

El manifiesto también conserva asociaciones para Citrix, enlaces Codex y
JetBrains cuando esas aplicaciones externas están instaladas. El módulo no las
instala; su ausencia no impide abrir los formatos básicos de la tabla.

En imv, `Shift++` amplía la imagen; `Shift+-` y `Ctrl+-` la reducen. Los dos
atajos de reducción se declaran explícitamente.

MPV conserva su selección normal de GPU. Awesome ejecuta aplicaciones gráficas
en X11 y no exporta `LIBGL_ALWAYS_SOFTWARE`.

## Efectos del instalador y diagnóstico

Además de enlazar `mimeapps.list`, configura el portal con GTK como proveedor
predeterminado y ejecuta `xdg-user-dirs-update`, que crea o actualiza nombres de
carpetas XDG del usuario.

```bash
xdg-mime query default inode/directory
xdg-mime query default application/pdf
systemctl --user status xdg-desktop-portal.service xdg-desktop-portal-gtk.service
gio mount -l
systemctl status udisks2.service
```

Si una aplicación muestra un selector incorrecto, comprueba `~/.config/xdg-desktop-portal/portals.conf` y reinicia los portales de usuario. Si un teléfono no aparece, desbloquéalo y selecciona MTP. Si faltan miniaturas, reinicia Thunar con `thunar -q` y ábrelo otra vez. No ejecutes Thunar como root.

## Fuentes del módulo

Instalador: [`setup/modules/files.sh`](../setup/modules/files.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
