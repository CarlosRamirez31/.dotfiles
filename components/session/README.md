# Session

Gestiona bloqueo, inactividad y energía con Hyprlock e Hypridle. El bloqueo usa
la misma paleta Tokyo Night, reloj grande y fondo difuminado. La pantalla se
atenúa a los 5 minutos, se bloquea a los 10, apaga monitores a los 11 y puede
suspender un equipo físico a los 30 minutos.

La suspensión automática se omite en máquinas virtuales y cuando existe una
sesión SSH entrante activa, evitando perder una máquina de trabajo remota. En
portátiles instala `power-profiles-daemon`, salvo que TLP ya esté administrando
la energía.

## Uso

```bash
./install.sh session
loginctl lock-session
systemctl --user status dotfiles-hypridle.service
```

Atajo: `Super+L` bloquea inmediatamente. Los tiempos se cambian en
`.config/hypr/hypridle.conf`.
