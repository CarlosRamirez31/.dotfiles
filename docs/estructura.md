# Organización y enlaces

La raíz sigue siendo `~/.dotfiles`. Cada aplicación encuentra sus archivos en
las rutas habituales mediante enlaces simbólicos declarados en `setup/links.tsv`.

| Fuente | Destino |
| --- | --- |
| `config/` | `~/.config/` |
| `home/` | `~/` |
| `bin/` | `~/.local/bin/` |
| `libexec/` | `~/.local/libexec/` |
| `share/` | `~/.local/share/` |
| `assets/fonts/` | `~/.local/share/fonts/` |
| `assets/wallpapers/` | `~/.config/wallpapers/` |
| `system/systemd/user/` | `~/.config/systemd/user/` |
| `system/sddm/` | Recursos copiados al sistema por el módulo SDDM |
| `environments/` | Recetas y recursos internos de Podman y Hermes |
| `setup/modules/` | Instalación por componente |
| `tests/` | Pruebas por componente |
| `docs/` | Guías de uso |

Cada fila de `setup/links.tsv` tiene tres columnas separadas por tabuladores:
**módulo**, **fuente relativa al repositorio**, **destino relativo al home**.
Se enlazan archivos individuales: `rofi` y `wallpaper` pueden compartir un
directorio sin instalarse mutuamente. Solo se instalan los módulos seleccionados.

`link_component` conserva los enlaces correctos y respalda un archivo ajeno
antes de reemplazarlo. Los ajustes privados no figuran en el manifiesto.
Para añadir un archivo administrado, añade también su fila y ejecuta `./check.sh`.

Mover o eliminar una fuente puede romper su enlace instalado. Tras cambiar una
ruta, actualiza el manifiesto, los consumidores y la instalación afectada.
Las herramientas temporales de la reorganización ya no forman parte del proyecto.
