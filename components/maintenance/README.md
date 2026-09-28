# Maintenance

Mantiene Arch estable sin instalar actualizaciones automáticamente. Activa el
timer semanal de `paccache`, que conserva las tres versiones recientes de cada
paquete, y `fstrim.timer` para almacenamiento compatible.

## Comandos

```bash
dotfiles-maintain check
dotfiles-maintain clean
dotfiles-maintain orphans
```

- `check` muestra servicios fallidos, espacio y actualizaciones disponibles.
- `clean` reduce la caché de Pacman y conserva 14 días del journal de usuario.
- `orphans` solo lista paquetes huérfanos; nunca los elimina automáticamente.

Las actualizaciones siguen siendo deliberadas mediante `update` (`pacman
-Syu`). Esto evita una actualización desatendida que deje Arch sin arrancar.
