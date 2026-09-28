# UWSM

Inicia Hyprland como una sesión systemd de usuario y exporta correctamente las
variables Wayland a aplicaciones y servicios. Define backend GTK, cursor,
terminal, escritorio, agente SSH y rutas de comandos personales.

VMware recibe solamente el renderer GTK compatible; las máquinas físicas
mantienen aceleración normal.

```bash
./install.sh uwsm
uwsm check may-start
```

Después de una instalación nueva selecciona `Hyprland (uwsm-managed)` en SDDM.
