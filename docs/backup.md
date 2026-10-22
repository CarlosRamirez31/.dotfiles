# Backup

Este componente proporciona copias del home con Restic. Está separado porque el destino y la contraseña son privados: prepara el programa y un respaldo semanal en una terminal flotante. La contraseña se introduce en esa terminal y no se guarda en un archivo.

Restic cifra antes de enviar, deduplica bloques y verifica integridad. La política conserva 7 snapshots diarios, 4 semanales y 6 mensuales y luego ejecuta `prune`.

## Primera configuración

```bash
./install.sh backup
backup setup /ruta/al/repositorio-restic
backup run
```

`setup` crea `backup.conf` con permisos `0600` y ejecuta `restic init`, que solicita y confirma la contraseña en la terminal sin guardarla. El timer semanal abre una terminal flotante que solicita la contraseña. No se inicia la copia hasta introducirla. El repositorio puede ser disco montado, ruta local o destino remoto admitido por Restic. Si está dentro de `$HOME`, se excluye automáticamente.

## Referencia de comandos

| Comando | Efecto |
| --- | --- |
| `backup setup REPOSITORY` | Inicializa el destino y solicita la contraseña sin guardarla. |
| `backup run` | Solicita la contraseña una vez, respalda las rutas y aplica retención. |
| `backup popup` | Abre la terminal flotante del respaldo programado. |
| `backup snapshots` | Lista snapshots, fechas, hosts y rutas. |
| `backup check` | Valida la estructura del repositorio. |
| `backup restore latest DESTINO` | Restaura el último snapshot aparte. |
| `backup restore ID DESTINO` | Restaura un snapshot específico. |

La restauración exige un directorio vacío separado. Rechaza el home, sus antecesores y cualquier destino con contenido:

```bash
backup restore latest /tmp/restore-home
find /tmp/restore-home -maxdepth 3 -type f | less
```

## Contenido y exclusiones

Por defecto `BACKUP_PATHS=("$HOME")`. Se excluyen cachés, papelera, contenedores, Steam, npm/Gradle, Android SDK, Flutter, `node_modules`, `target/debug` y la contraseña Restic: son datos regenerables, voluminosos o secretos que no deben entrar al repositorio.

Para limitar las rutas, edita el `backup.conf` privado:

```bash
BACKUP_PATHS=("$HOME/Documents" "$HOME/Pictures" "$HOME/.ssh")
```

## Archivos y automatización

| Archivo | Propósito |
| --- | --- |
| `.local/bin/dotfiles-backup` | Interfaz Restic y política de retención. |
| `.config/dotfiles/backup-excludes` | Patrones excluidos. |
| `.config/dotfiles/backup.conf.example` | Ejemplo versionado sin secretos. |
| `.config/systemd/user/dotfiles-backup.service` | Trabajo `oneshot` con prioridad baja. |
| `.config/systemd/user/dotfiles-backup.timer` | Semanal, persistente y con demora aleatoria de hasta 30 min. |

`backup.conf` y el antiguo nombre `restic-password` están ignorados por Git. No se crea ningún archivo de contraseña. El timer abre una terminal flotante y espera la contraseña. Se conserva solo en la memoria de los procesos durante la copia y la retención. El resultado queda visible hasta pulsar Enter. Solo se abre una ventana a la vez. Si falta el repositorio local, solicita y confirma una contraseña nueva antes de crearlo. Con `BACKUP_DISK_UUID` configurado, intenta montar ese disco y comprueba que corresponda al destino; si falla, muestra el error sin iniciar la copia. Las variables `RESTIC_PASSWORD`, `RESTIC_PASSWORD_FILE` y `RESTIC_PASSWORD_COMMAND` se descartan al cargar la configuración.

## Diagnóstico

```bash
systemctl --user status dotfiles-backup.timer
systemctl --user list-timers dotfiles-backup.timer
journalctl --user -u dotfiles-backup.service
backup check
```

Si el destino es externo debe estar montado. Un fallo no borra snapshots; corrige montaje/credenciales y ejecuta `backup run`.

## Fuentes del módulo

Instalador: [`setup/modules/backup.sh`](../setup/modules/backup.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
