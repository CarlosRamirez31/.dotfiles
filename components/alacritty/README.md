# Alacritty

Configura una terminal Wayland limpia con JetBrainsMono Nerd Font y Zsh como
shell de inicio. Registra además `Alacritty.desktop`, el terminal preferido de
XDG y el wrapper `dotfiles-terminal`, usado por Hyprland y HyprPanel.

## Uso

```bash
./install.sh alacritty
dotfiles-terminal
```

Los atajos para abrirla son `Alt+Enter` y `Ctrl+Alt+T`. El aspecto vive en
`dotfiles/.config/alacritty/alacritty.toml`; el shell se configura por separado
en `components/shell`.
