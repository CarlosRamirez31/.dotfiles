# Doctor

Es la comprobación final del escritorio. Revisa programas, enlaces Stow, shell,
servicios del sistema, sockets de credenciales, timers, contenedores, respaldo
y errores de la configuración Hyprland activa.

```bash
dotfiles-doctor
./install.sh doctor
```

Un error indica que falta una pieza esencial; una advertencia señala una
función instalada pero inactiva. El destino de Restic y la identidad Git se
muestran como pendientes informativos porque contienen decisiones privadas.
