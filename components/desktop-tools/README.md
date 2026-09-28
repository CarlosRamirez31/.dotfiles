# Desktop tools

Reúne capturas Wayland y un historial local del portapapeles. Grim toma la
imagen, Slurp permite elegir región, Swappy anota y Cliphist conserva texto e
imágenes mediante dos servicios de usuario.

## Atajos

- `Print`: pantalla completa y copia al portapapeles.
- `Alt+Print`: elegir región.
- `Alt+Shift+S`: elegir región y editarla.
- `Alt+C`: buscar el historial con Rofi.

Las capturas se guardan en `Pictures/Screenshots`. Para borrar el historial de
forma confirmada:

```bash
dotfiles-clipboard-clear
```

Instalación y estado:

```bash
./install.sh desktop-tools
systemctl --user status dotfiles-cliphist-text.service
```
