# Wallpaper

Instala Awww y el fondo Arch incluido en el repositorio. El daemon se inicia
con Hyprland y la imagen se aplica sin transición para que el acceso sea limpio
y reproducible.

```bash
./install.sh wallpaper
awww img ~/.config/wallpapers/arch-bsod.png
```

Para reemplazar el fondo cambia el archivo administrado y la ruta usada en
`components/hyprland/dotfiles/.config/hypr/lua/core.lua`.
