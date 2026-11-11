# Files

Este componente convierte el escritorio mínimo en un entorno capaz de navegar archivos, montar medios y abrir formatos comunes. Yazi aporta navegación de terminal y el selector de archivos del portal; GTK cubre las otras funciones del portal y Thunar permanece como gestor gráfico. Las asociaciones MIME permiten que Rofi, Brave y aplicaciones GTK elijan programas predecibles.

## Paquetes y responsabilidades

| Paquete | Función |
| --- | --- |
| `yazi` | Gestor de terminal con previsualizaciones y navegación `h/j/k/l`. |
| `thunar`, `thunar-volman` | Gestor de archivos y reacción a medios removibles. |
| `tumbler` | Miniaturas en Thunar. |
| `gvfs`, `gvfs-mtp`, `gvfs-gphoto2`, `gvfs-smb` | Papelera, teléfonos, cámaras y recursos SMB. |
| `android-tools`, `android-udev` | ADB y reglas de permisos USB para depurar dispositivos Android. |
| `udisks2` | Montaje de discos por sesión sin ejecutar Thunar como root. |
| `file-roller` | Crear/extraer ZIP, 7z, RAR y tar. |
| `imv` | Visor de imágenes. |
| `mpv` | Audio y vídeo. |
| `ffmpeg`, `poppler`, `resvg`, `imagemagick` | Fotogramas de vídeo y vistas previas de PDF, SVG y formatos de imagen. |
| `zathura`, `zathura-pdf-mupdf` | PDF y backend MuPDF. |
| `tesseract-data-eng`, `tesseract-data-spa` | OCR inglés/español requerido por MuPDF. |
| `xdg-user-dirs` | Resuelve Documents, Downloads, Pictures y Videos según idioma. |
| `xdg-desktop-portal-termfilechooser` (AUR) | Conecta los diálogos de abrir, subir, elegir carpeta y guardar con Yazi. |

## Uso

```bash
./install.sh files
yazi
xdg-open documento.pdf
xdg-open imagen.png
gio mount smb://servidor/recurso
```

`Alt+E` abre Yazi en Kitty y `Ctrl+Alt+E` abre Thunar. En Yazi se navega
con `h/j/k/l`, `Enter` o `Shift+Enter` abre el archivo seleccionado,
`l` entra en directorios, `Space` selecciona y `q` sale. `gd`, `gp` y `gh`
saltan a Descargas, Imágenes y el directorio personal. Los volúmenes aparecen
en la barra lateral de Thunar y se montan mediante UDisks/GVfs; no hace falta
`sudo mount` para el uso normal.

En Awesome/X11, las aplicaciones compatibles abren Yazi al subir, abrir o guardar
archivos mediante el portal. `GTK_USE_PORTAL=1` se configura para las aplicaciones
de la sesión; las que ya estaban abiertas pueden necesitar reiniciarse. Una
aplicación que utiliza su propio selector en lugar del portal no queda controlada
por esta configuración. Yazi también sigue disponible con `Alt+E`.

## Copiar, cortar, arrastrar y reunir archivos

En la lista de archivos de Yazi, `Space` marca varios archivos. `Ctrl+C` pone
la selección (o el archivo bajo el cursor si no hay selección) en el portapapeles
de archivos del sistema. En Thunar u otra aplicación compatible, `Ctrl+V` pega
los archivos. En el propio Yazi, **Ctrl+V** pega en la carpeta que estás viendo,
tanto si copiaste como si cortaste desde File tray, Yazi u otro gestor compatible.
El pegado usa el motor de transferencias de Thunar, sin abrir su navegador;
conserva el progreso y los diálogos de conflicto. `Ctrl+X` prepara un corte: los archivos se mueven cuando el destino
acepta y ejecuta el pegado. Estos atajos conservan la selección y no alteran
los campos para editar nombres; `y`/`x` y `p` siguen siendo los controles
propios de Yazi. `Ctrl+Shift+C` de Kitty conserva su copia de texto.

| Acción en Yazi | Atajo |
| --- | --- |
| Copiar archivos al portapapeles del sistema conservando la selección | `Ctrl+C` |
| Preparar el corte para pegar dentro o fuera de Yazi | `Ctrl+X` |
| Pegar archivos copiados o cortados del portapapeles en la carpeta actual | `Ctrl+V` |
| Añadir archivos a la bandeja temporal | `Alt+A` |

Para arrastrar, mantén el botón izquierdo sobre uno de los archivos seleccionados
y llévalo a una aplicación que acepte archivos. No mantengas Shift: Kitty reserva
esa tecla para seleccionar texto del terminal. Se usa el DnD nativo de
[Yazi](https://yazi-rs.github.io/docs/dnd/) y Kitty, sin herramientas adicionales.

`Alt+A` dentro de Yazi añade los archivos seleccionados a **File tray**.
`Alt+A` muestra brevemente los archivos añadidos en un panel compacto que sale
animado desde abajo. Se oculta solo al terminar de interactuar; pasar el puntero
encima o mantener un arrastre lo conserva abierto.

`Alt+Shift+F8` abre ese mismo panel desde cualquier ventana y lo mantiene visible
para revisarlo. El mismo atajo, **×** o `Esc` con el panel enfocado lo cierran con
animación. Puedes ir a otra carpeta y añadir más archivos. La bandeja conserva hasta 500 referencias únicas
en memoria durante la sesión; no duplica el contenido ni guarda una lista en disco.

| Acción en File tray | Control |
| --- | --- |
| Copiar filas seleccionadas, o todas si no hay selección | `Ctrl+C` o **Copy** |
| Preparar corte para pegar en otro gestor de archivos | `Ctrl+X` o **Cut** |
| Seleccionar todas las filas | `Ctrl+A` |
| Retirar filas de la bandeja sin borrar originales | `Delete` o **Remove** |
| Vaciar las referencias sin borrar originales | **Clear** |
| Ocultar conservando la bandeja | `Esc` |

Durante un arrastre desde Yazi u otra aplicación, acerca los archivos al centro
del borde inferior de la pantalla: el panel se revela sin interrumpir el arrastre.
Puedes soltarlos sobre el borde o dentro del panel para añadirlos a la bandeja.
La apertura funciona en cada monitor y no se activa al pasar el puntero sin archivos.

La tarjeta inferior permite arrastrar la selección de la bandeja; también puedes
soltar archivos sobre ella para añadirlos. El arrastre de la bandeja anuncia copia.
El destino decide cómo procesar la entrega. La copia/corte publica los formatos
URI-list, GNOME y KDE para ampliar la compatibilidad; una aplicación que solo
acepta texto puede recibir las rutas. En sesiones remotas como Citrix, la
transferencia depende además de las capacidades y políticas del cliente/servidor.
El portapapeles sigue disponible tras cerrar Yazi mientras conserve su propietario.

## Vistas previas y apertura desde Yazi

Kitty muestra las vistas previas con su protocolo gráfico nativo, detectado por
Yazi. Se conservan los motores incluidos: imágenes, SVG con resvg, fotogramas de
vídeo con FFmpeg y páginas PDF con pdftoppm. No se necesitan plugins adicionales.
Los vídeos se previsualizan como fotogramas; la reproducción completa ocurre en mpv.

`J` y `K` avanzan o retroceden la vista previa, incluidas páginas PDF y posiciones
del vídeo. `Enter` abre imágenes y SVG en imv, audio/vídeo en mpv y PDF en Zathura.
`O` (mayúscula) muestra «Abrir con», que también conserva la aplicación del sistema.
Las selecciones múltiples se pasan como rutas independientes mediante los
placeholders nativos de Yazi. El modo `--chooser-file` también muestra las vistas
previas y devuelve la ruta elegida, sin lanzar el visor al confirmar el archivo.

La configuración vive en `config/yazi/yazi.toml`. Las reglas se añaden delante de
las originales; los restantes tipos de archivo conservan el comportamiento de Yazi.

## Selector del portal

`dotfiles-filechooser` crea una sesión privada y temporal de Yazi por solicitud.
Reutiliza tema, vistas previas y configuración de archivos. Los atajos de
confirmación y el título de la ventana solo se aplican en el selector.

| Acción | Control en el selector |
| --- | --- |
| Entrar/salir de una carpeta | `l` / `h`, o flechas derecha/izquierda |
| Confirmar archivo(s), carpeta actual o destino de guardado | `Enter` o `Ctrl+S` |
| Cambiar el nombre propuesto de la descarga | `F2`, solo al guardar |
| Renombrar un archivo existente | `r` |
| Cortar y pegar/mover archivos existentes | `x`, navegar y `p` |
| Copiar y pegar | `y`, navegar y `p` |
| Crear carpeta | `a`, escribir el nombre terminado en `/` |
| Marcar archivos para una selección múltiple | `Space` |
| Descargas / Imágenes / carpeta personal | `gd` / `gp` / `gh` |
| Cancelar | `q` o cerrar la ventana |

Al guardar, la cabecera `SAVE AS` muestra el nombre; `F2` permite editarlo, y
`Enter` devuelve esa ruta dentro de la carpeta actual. Si ya existe, se pide
confirmación antes de devolverla. La aplicación que descarga escribe el contenido;
el selector no crea un archivo provisional. Renombrar, cortar y pegar archivos
existentes modifica esos archivos en el momento de realizar la operación.

Los títulos y mensajes del selector están en inglés. El plugin local `portal-picker`
solo se carga en la sesión de la solicitud. Los nombres se pasan como argumentos
independientes, sin evaluarlos en un shell.

## Asociaciones predeterminadas del sistema

| Contenido | Aplicación |
| --- | --- |
| Directorios | Thunar |
| HTTP, HTTPS y HTML | Brave |
| PDF | OnlyOffice (Zathura al abrir desde Yazi) |
| BMP, GIF, JPEG, PNG, SVG y WebP | imv |
| FLAC, MP3, Ogg y vídeos comunes | mpv |
| ZIP, 7z, RAR y tar | File Roller |

Se declaran en `.config/mimeapps.list`. Brave viene de `desktop-extras`; si ese componente no está instalado, la asociación queda preparada pero no podrá abrirse hasta instalarlo.

El manifiesto también conserva asociaciones para Citrix, enlaces Codex y
JetBrains cuando esas aplicaciones externas están instaladas. El módulo no las
instala; su ausencia no impide abrir los formatos básicos de la tabla.

En imv, `Shift++` amplía la imagen; `Shift+-` y `Ctrl+-` la reducen. Los dos
atajos de reducción se declaran explícitamente.

MPV conserva su selección normal de GPU. Awesome ejecuta aplicaciones gráficas
en X11 y no exporta `LIBGL_ALWAYS_SOFTWARE`.

## Efectos del instalador y diagnóstico

Además de enlazar `mimeapps.list`, instala el backend de AUR mediante el helper
del proyecto y configura `FileChooser=termfilechooser;gtk`. GTK sigue siendo el
proveedor general y el respaldo. Ejecuta `xdg-user-dirs-update`, que crea o actualiza
nombres de carpetas XDG del usuario.

```bash
xdg-mime query default inode/directory
xdg-mime query default application/pdf
systemctl --user status xdg-desktop-portal.service xdg-desktop-portal-termfilechooser.service
gio mount -l
systemctl status udisks2.service
```

Si una aplicación muestra un selector incorrecto, comprueba `~/.config/xdg-desktop-portal/portals.conf` y reinicia los portales de usuario. Si un teléfono no aparece, desbloquéalo y selecciona MTP. Si faltan miniaturas, reinicia Thunar con `thunar -q` y ábrelo otra vez. No ejecutes Thunar como root.

## Fuentes del módulo

Instalador: [`setup/modules/files.sh`](../setup/modules/files.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
