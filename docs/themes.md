# Themes

Este componente instala los recursos visuales externos compartidos por Awesome y aplicaciones GTK. Se mantiene separado porque ambos paquetes proceden del AUR y no son necesarios para una instalación puramente funcional.

## Recursos

| Paquete AUR | Uso |
| --- | --- |
| `bibata-cursor-theme` | Cursor `Bibata-Modern-Classic`, tamaño 24 en Awesome/X11. |
| `oranchelo-icon-theme-git` | Iconos GTK Oranchelo. |

El instalador busca `paru` y luego `yay`. Si no existe ninguno, instala `git` y `base-devel`, compila `yay-bin` en un directorio temporal y lo utiliza para instalar los temas. Los paquetes ya presentes se omiten.

## Instalación y comprobación

```bash
./install.sh themes
pacman -Q bibata-cursor-theme oranchelo-icon-theme-git
find /usr/share/icons -maxdepth 1 -iname '*bibata*' -o -iname '*oranchelo*'
```

Awesome carga Bibata desde `.Xresources` y configura las aplicaciones GTK con `Bibata-Modern-Classic`, tamaño 24. También selecciona Oranchelo como tema de iconos GTK.

Este componente no escribe preferencias GTK de usuario ni descarga fondos. El wallpaper pertenece a `wallpaper`, las fuentes a `fonts` y los colores están definidos en cada aplicación.


Si el cursor anterior persiste, cierra la sesión X11 completa y vuelve a entrar para recargar los recursos Xcursor.

## Fuentes del módulo

Instalador: [`setup/modules/themes.sh`](../setup/modules/themes.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
