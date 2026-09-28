# Backup

Este componente proporciona copias del home con Restic. Está separado porque el destino y la contraseña son privados: prepara programa, comando y timer, pero nunca inventa un repositorio ni guarda secretos en Git.

Restic cifra antes de enviar, deduplica bloques y verifica integridad. La política conserva 7 snapshots diarios, 4 semanales y 6 mensuales y luego ejecuta `prune`.

## Primera configuración

```bash
./install.sh backup
dotfiles-backup setup /ruta/al/repositorio-restic
dotfiles-backup run
```

`setup` solicita y confirma contraseña, crea `restic-password` y `backup.conf` con permisos `0600`, ejecuta `restic init` y habilita el timer. El repositorio puede ser disco montado, ruta local o destino remoto admitido por Restic. Si está dentro de `$HOME`, se excluye automáticamente.

## Referencia de comandos

| Comando | Efecto |
| --- | --- |
| `dotfiles-backup setup REPOSITORY` | Inicializa destino, contraseña y timer. |
| `dotfiles-backup run` | Respalda las rutas y aplica retención. |
| `dotfiles-backup snapshots` | Lista snapshots, fechas, hosts y rutas. |
| `dotfiles-backup check` | Valida la estructura del repositorio. |
| `dotfiles-backup restore latest DESTINO` | Restaura el último snapshot aparte. |
| `dotfiles-backup restore ID DESTINO` | Restaura un snapshot específico. |

La restauración exige destino y nunca sobrescribe el home directamente:

```bash
dotfiles-backup restore latest /tmp/restore-home
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

`backup.conf` y `restic-password` están ignorados por Git. `Persistent=true` ejecuta una copia pendiente al volver a encender.

## Diagnóstico

```bash
systemctl --user status dotfiles-backup.timer
systemctl --user list-timers dotfiles-backup.timer
journalctl --user -u dotfiles-backup.service
dotfiles-backup check
```

Si el destino es externo debe estar montado. Un fallo no borra snapshots; corrige montaje/credenciales y ejecuta `dotfiles-backup run`.
