# Files

Instala Thunar como gestor de archivos, Tumbler para miniaturas, GVfs/UDisks
para papelera y dispositivos USB/MTP/SMB, y File Roller para archivos
comprimidos. Imv abre imágenes, mpv reproduce audio/vídeo y Zathura abre PDF.

MuPDF incorpora OCR; los datos de Tesseract para inglés y español están
declarados explícitamente para que Pacman no muestre una lista de idiomas.
Firefox queda como aplicación HTTP/HTML cuando se instala `desktop-extras`.

## Uso

```bash
./install.sh files
thunar
```

Atajo: `Alt+E`. Las asociaciones viven en `.config/mimeapps.list`; medios
removibles aparecen en la barra lateral de Thunar.
