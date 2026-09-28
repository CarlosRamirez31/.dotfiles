# Themes

Este componente instala los recursos visuales externos compartidos por compositor, panel, bloqueo y aplicaciones GTK. Se mantiene separado porque ambos paquetes proceden del AUR y no son necesarios para una instalación puramente funcional.

## Recursos

| Paquete AUR | Uso |
| --- | --- |
| `bibata-cursor-theme` | Cursor `Bibata-Modern-Classic` usado por Wayland/XWayland. |
| `oranchelo-icon-theme-git` | Iconos disponibles para aplicaciones y selectores GTK. |

El instalador busca `paru` y luego `yay`. Si no existe ninguno, instala `git` y `base-devel`, compila `yay-bin` en un directorio temporal y lo utiliza para instalar los temas. Los paquetes ya presentes se omiten.

## Instalación y comprobación

```bash
./install.sh themes
pacman -Q bibata-cursor-theme oranchelo-icon-theme-git
find /usr/share/icons -maxdepth 1 -iname '*bibata*' -o -iname '*oranchelo*'
```

`uwsm` exporta Bibata como `XCURSOR_THEME` y `HYPRCURSOR_THEME`, tamaño 24. Hyprland fuerza ese cursor al iniciar y desactiva su backend Hyprcursor para usar una única fuente XCursor consistente.

Este componente no escribe preferencias GTK de usuario ni descarga fondos. El wallpaper pertenece a `wallpaper`, las fuentes a `fonts` y los colores están definidos en cada aplicación.

Bibata sí queda seleccionado por las variables de UWSM. Oranchelo queda
instalado y disponible, pero este repositorio no fuerza globalmente
`gtk-icon-theme-name`; así no sobrescribe una preferencia GTK que el usuario
haya elegido fuera de los dotfiles.

Si el cursor anterior persiste, cierra la sesión completa y vuelve a entrar: las variables de cursor se importan al iniciar UWSM y no todas las aplicaciones aceptan cambios en caliente.
