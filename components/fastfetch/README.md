# Fastfetch

Instala Fastfetch y una tarjeta de diagnóstico visual. Muestra el contexto de la máquina y sesión al abrir Zsh, con menor coste y mantenimiento activo frente a Neofetch.

## Información mostrada

Usa logo Arch y presenta usuario/host, sistema, equipo, kernel, uptime, paquetes, shell, pantalla, compositor, terminal, fuente, CPU, GPU, memoria, disco raíz, IP local, batería e idioma. Los módulos no aplicables se omiten naturalmente.

## Uso

```bash
./install.sh fastfetch
fastfetch
sysinfo                    # alias del componente shell
fastfetch --pipe false
```

Zsh lo ejecuta al abrir una terminal interactiva conectada a TTY. Para omitirlo en una terminal:

```bash
DOTFILES_FASTFETCH=0 zsh
```

Para desactivarlo persistentemente exporta esa variable antes de `.zshrc`.

## Archivo y validación

`.config/fastfetch/config.jsonc` define orden, iconos y Tokyo Night. El instalador lo valida silenciosamente; una sintaxis inválida hace fallar la instalación en vez de romper cada terminal nueva.

```bash
fastfetch --config ~/.config/fastfetch/config.jsonc
fastfetch --list-modules
```

Los glifos requieren `fonts`. El alias `sysinfo` y arranque automático pertenecen a `shell`; Fastfetch funciona también por separado.
