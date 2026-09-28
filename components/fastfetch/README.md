# Fastfetch

Muestra al iniciar Zsh una tarjeta compacta con Arch, kernel, Hyprland,
terminal, CPU/GPU, memoria, disco, red y batería cuando existe. Sustituye a
Neofetch porque inicia más rápido y continúa mantenido.

## Uso

```bash
fastfetch
sysinfo
```

Para no mostrarla automáticamente en una terminal concreta:

```bash
DOTFILES_FASTFETCH=0 zsh
```

El diseño se cambia en `dotfiles/.config/fastfetch/config.jsonc`.
