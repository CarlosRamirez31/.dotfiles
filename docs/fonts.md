# Fonts

Este componente instala las dos familias tipográficas que sostienen la interfaz: JetBrainsMono Nerd Font para terminal/código/iconos y Lexend para Awesome. Tenerlas en un módulo temprano evita cuadros vacíos y cambios de medida durante el resto de la instalación.

## Contenido

| Fuente | Procedencia | Uso |
| --- | --- | --- |
| JetBrainsMono Nerd Font | Paquete Arch `ttf-jetbrains-mono-nerd` | Alacritty, Starship e iconos Nerd Font. |
| Iosevka Nerd Font | Paquete Arch `ttf-iosevka-nerd` | Tipografía compacta de la barra inspirada en Ayamir/Yoru. |
| Material Icons | Paquete Arch `ttf-material-icons` | Iconos de controles de la barra Ayamir/Yoru. |
| Noto Color Emoji | Paquete Arch `noto-fonts-emoji` | Emojis de Starship, incluido el dragón que identifica Kali Linux. |
| Lexend Variable | Archivo versionado bajo `.local/share/fonts/Lexend` | Texto y controles de Awesome. |

El archivo `OFL.txt` conserva la licencia de Lexend junto a la fuente. El instalador añade `fontconfig`, enlaza los archivos y fuerza `fc-cache -f` para que aplicaciones ya instaladas puedan descubrirlos.

## Instalación y comprobación

```bash
./install.sh fonts
fc-match "JetBrainsMono Nerd Font"
fc-match "Noto Color Emoji"
fc-match Lexend
fc-list | rg 'JetBrains|Lexend'
```

`fc-match` debe devolver la familia solicitada y no una sustitución como DejaVu Sans. Después de instalar, aplicaciones antiguas pueden necesitar reiniciarse para reconstruir sus propias cachés. Alacritty usa Noto Color Emoji como respaldo cuando Starship muestra símbolos Unicode que no pertenecen a Nerd Fonts.

## Relaciones y personalización

Alacritty solicita estilos SemiBold/Bold de JetBrainsMono y Awesome solicita Lexend de peso 500. Cambiar el nombre o retirar una familia exige actualizar esas configuraciones para evitar fallback inconsistente.

Si aparecen glifos cuadrados, verifica primero que el proceso use esta cuenta de usuario y ejecuta:

```bash
fc-cache -rv
fc-match -v "JetBrainsMono Nerd Font" | less
```
