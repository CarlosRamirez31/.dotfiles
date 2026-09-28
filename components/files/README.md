# Files

Este componente convierte el escritorio mínimo en un entorno capaz de navegar archivos, montar medios y abrir formatos comunes. Centraliza las asociaciones MIME para que Rofi, Firefox, Thunar y aplicaciones GTK elijan programas predecibles.

## Paquetes y responsabilidades

| Paquete | Función |
| --- | --- |
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
thunar
xdg-open documento.pdf
xdg-open imagen.png
gio mount smb://servidor/recurso
```

`Alt+E` abre Thunar. Los volúmenes aparecen en su barra lateral y se montan mediante UDisks/GVfs; no hace falta `sudo mount` para el uso normal.

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

## Efectos del instalador y diagnóstico

Además de enlazar `mimeapps.list`, ejecuta `xdg-user-dirs-update`, que crea o actualiza nombres de carpetas XDG del usuario.

```bash
xdg-mime query default inode/directory
xdg-mime query default application/pdf
gio mount -l
systemctl status udisks2.service
```

Si un teléfono no aparece, desbloquéalo y selecciona MTP. Si faltan miniaturas, reinicia Thunar con `thunar -q` y ábrelo otra vez. No ejecutes Thunar como root: rompería permisos y el contexto de la sesión.
