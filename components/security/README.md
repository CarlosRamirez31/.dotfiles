# Security

Este componente configura almacenamiento de credenciales, agente SSH y un firewall nftables de estación de trabajo. La política permite uso normal saliente y bloquea conexiones entrantes nuevas, con una excepción temporal y limitada para laboratorios por VPN.

## Credenciales y agente SSH

Instala GNOME Keyring, libsecret, Seahorse y GCR 4. Habilita los sockets de usuario `gnome-keyring-daemon.socket` y `gcr-ssh-agent.socket`; `shell` exporta `SSH_AUTH_SOCK=$XDG_RUNTIME_DIR/gcr/ssh`.

```bash
systemctl --user status gnome-keyring-daemon.socket gcr-ssh-agent.socket
ssh-add -L
seahorse
```

Seahorse permite inspeccionar credenciales; este componente no crea llaves ni contraseñas automáticamente.

## Política del firewall

La tabla `inet dotfiles_filter` aplica:

- input con política `drop`;
- descarte de estados inválidos;
- aceptación de tráfico establecido/relacionado y loopback;
- ICMP/ICMPv6 para diagnóstico y operación de red;
- respuestas DHCP IPv4/IPv6;
- output y forward permitidos;
- puertos de laboratorio solo en interfaces cuyo nombre empieza por `tun`.

## Comandos

```bash
lab-firewall enable
lab-firewall status
lab-firewall disable
lab-firewall lab-open tcp 4444
lab-firewall lab-close tcp 4444
```

`enable` valida la sintaxis con `nft --check`, respalda `/etc/nftables.conf` si difiere, instala el archivo con modo `0600`, habilita el servicio y lo reinicia. `disable` apaga el servicio y elimina únicamente la tabla administrada.

`lab-open` acepta `tcp` o `udp` y puertos 1–65535. La apertura solo recibe tráfico por `tun*`; no expone el listener en Wi-Fi/Ethernet. Los sets son efímeros y se vacían tras recargar nftables o reiniciar.

## Seguridad de instalación remota

Durante una instalación detectada mediante `$SSH_CONNECTION`, los archivos se instalan pero el firewall no se activa para evitar cortar acceso remoto. Revísalo y ejecuta `lab-firewall enable` localmente.

## Diagnóstico y recuperación

```bash
sudo nft list ruleset
sudo nft --check --file ~/.config/dotfiles/nftables.conf
systemctl status nftables.service
journalctl -u nftables.service -b
```

Antes de cambiar reglas en un host remoto mantén una segunda vía de acceso. Los backups de `/etc/nftables.conf` llevan fecha/hora y no se eliminan automáticamente.
