# Reestructuración del repositorio

La configuración continúa en `~/.dotfiles`. Cambian sus rutas internas; los
archivos instalados conservan sus destinos, nombres y permisos.

## Mapa

| Contenido | Fuente | Destino habitual |
| --- | --- | --- |
| Aplicaciones | `config/` | `~/.config/` |
| Inicio de sesión y shell | `home/` | `~/` |
| Comandos | `bin/` | `~/.local/bin/` |
| Auxiliares | `libexec/` | `~/.local/libexec/` |
| Lanzadores y datos | `share/` | `~/.local/share/` |
| Servicios de usuario | `system/systemd/user/` | `~/.config/systemd/user/` |
| Tema de acceso | `system/sddm/` | Instalación explícita del módulo SDDM |
| Fuentes | `assets/fonts/` | `~/.local/share/fonts/` |
| Fondos | `assets/wallpapers/` | `~/.config/wallpapers/` |
| Contenedores | `environments/` | Según el entorno |
| Instaladores | `setup/modules/` | Se ejecutan mediante `install.sh` |
| Documentación | `docs/` | Permanece en el repositorio |
| Pruebas | `tests/` | Se ejecutan desde la raíz |

`setup/links.tsv` es la fuente de verdad para los 170 archivos administrados.
Cada fila contiene módulo, fuente relativa al repositorio y destino relativo al
home. Instalar Rofi no instala el selector de fondos aunque compartan carpeta.
Hermes y los otros módulos opcionales conservan su selección explícita.

Los recursos internos de Hermes y el tema de SDDM conservan sus subdivisiones.
Los servicios de batería y recuperación de GPU en `share/` mantienen sus destinos
porque sus instaladores y programas los utilizan allí.

## Migrar una instalación existente

Una rama separada conserva el historial, pero cambiar las rutas dentro del mismo
checkout puede dejar temporalmente enlaces rotos. Primero prepara y verifica la
reestructuración en otro worktree. No ejecutes una instalación completa para
migrar los enlaces: podría instalar paquetes o reiniciar servicios.

Después de cambiar el checkout a la rama nueva:

```bash
python3 -B setup/migrate-links.py
python3 -B setup/migrate-links.py --apply --log /tmp/dotfiles-links-before.json
```

La vista previa no modifica enlaces. La aplicación solo reemplaza enlaces ya
existentes que apuntan al esquema anterior dentro de este mismo repositorio.
Incluye enlaces de directorios y unidades habilitadas en systemd. Conserva los
archivos normales, los enlaces ajenos y los módulos que no estaban instalados.
No instala paquetes, inicia servicios, modifica perfiles ni recrea contenedores.

El registro guarda los destinos exactos anteriores. Para volver a `AwesomeVM`,
conserva primero una copia del script fuera del checkout, cambia de rama y
restaura los enlaces con esa copia:

```bash
cp setup/migrate-links.py /tmp/dotfiles-migrate-links.py
git switch AwesomeVM
python3 -B /tmp/dotfiles-migrate-links.py --restore /tmp/dotfiles-links-before.json --apply
```

No cambies de rama con trabajo sin guardar. El registro pertenece al equipo donde
se creó; no lo añadas a Git. Los cambios de rama y enlaces se hacen consecutivamente
para reducir el intervalo en que alguna ruta puede estar temporalmente ausente.

## Verificar

```bash
./install.sh --dry-run all
./install.sh --dry-run hermes flutter rider docker dbeaver voice-isolation
python3 -B -m unittest discover -s tests/setup
python3 -B -m unittest discover -s tests/workbench
./check.sh
```

Las demás pruebas Python se ejecutan por carpeta con
`python3 -B -m unittest discover -s tests/NOMBRE`.
Las pruebas Lua de Awesome se ejecutan con `lua tests/awesome/ARCHIVO.lua` y
las de Neovim con `nvim --headless -u NONE -i NONE -l tests/nvim/ARCHIVO.lua`.
La comprobación general también informa problemas heredados de formato y
ShellCheck; compara con la rama de origen antes de atribuirlos a esta migración.
