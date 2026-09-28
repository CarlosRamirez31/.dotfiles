# Backup

Instala Restic para copias cifradas, deduplicadas y verificables. Protege el
home completo salvo cachés, descargas técnicas regenerables, SDK grandes y el
propio archivo de contraseña. Conserva siete copias diarias, cuatro semanales y
seis mensuales.

El repositorio y la contraseña son privados: `backup.conf` y
`restic-password` están ignorados por Git. El timer no se habilita hasta que
exista un destino real.

## Primera configuración

Usa un disco externo montado, NAS o repositorio Restic remoto:

```bash
dotfiles-backup setup /ruta/al/repositorio
dotfiles-backup run
```

## Uso habitual

```bash
dotfiles-backup snapshots
dotfiles-backup check
dotfiles-backup restore latest /tmp/restore
```

La restauración siempre apunta a un directorio aparte para no sobrescribir el
home accidentalmente. El servicio `dotfiles-backup.timer` ejecuta una copia
semanal después de completar `setup`.
