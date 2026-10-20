# DBeaver opcional en dev

```bash
./install.sh dbeaver
dbeaver
```

Instala DBeaver Community y sus dependencias gráficas/Java dentro de `dev`, solo al seleccionarlo explícitamente. `all` y la instalación normal lo excluyen. El comando funciona desde dentro y fuera de `dev`, devuelve la terminal de inmediato y permite cerrarla sin cerrar el editor. También aparece en el menú de aplicaciones como **DBeaver (dev)**.

Las conexiones y preferencias se conservan en el home compartido. Las credenciales se introducen en DBeaver; no se guardan en los dotfiles. La salida del arranque está en `~/.cache/dbeaver-dev/launcher.log`.
