# HyprPanel

Proporciona barra, bandeja, menús rápidos y notificaciones. Muestra siempre los
cuatro workspaces generales y distingue vacío, ocupado y activo. También añade
el estado HTB verde con dirección IP cuando una VPN compatible está conectada.

## HTB

El panel detecta OpenVPN y la interfaz `tun*`. Para asociar manualmente la IP
de una máquina objetivo:

```bash
dotfiles-htb-target 10.10.11.20
dotfiles-htb-target clear
```

```bash
./install.sh hyprpanel
```

Las plantillas están en `templates/`; el instalador las copia al directorio de
ejecución de HyprPanel y reinicia solamente el panel activo.
