# Security

Configura GNOME Keyring, el agente SSH de GCR y un firewall nftables para una
estación de trabajo. Se aceptan conexiones establecidas, loopback, DHCP e ICMP;
las conexiones entrantes nuevas se bloquean.

Durante una instalación por SSH el firewall no se activa automáticamente, para
no cortar la sesión. La configuración anterior de `/etc/nftables.conf` se
respalda antes de reemplazarla.

## HTB y laboratorios

Las conexiones que tú inicias hacia HTB funcionan sin cambios. Solo abre un
puerto cuando la máquina remota deba conectarse de vuelta, y únicamente quedará
expuesto en interfaces VPN `tun*`:

```bash
dotfiles-firewall lab-open tcp 4444
dotfiles-firewall lab-close tcp 4444
dotfiles-firewall status
```

Los puertos de laboratorio son temporales y desaparecen al reiniciar o recargar
el firewall. `dotfiles-firewall enable` lo instala/activa localmente.
