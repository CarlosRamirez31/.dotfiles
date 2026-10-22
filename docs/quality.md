# Validación del repositorio

`./install.sh quality` instala ShellCheck, shfmt, jq, Lua, Zsh, Python, PyYAML y Neovim.
`./check.sh` ejecuta las comprobaciones desde cualquier directorio y devuelve
código 1 si falla alguna familia; continúa para mostrar también los otros fallos.

```bash
./check.sh
python3 -B setup/validate.py  # sintaxis Python/TOML/JSONC, manifiesto y enlaces locales
python3 -B tests/run.py      # todas las suites Python y Lua
```

## Cobertura

- Bash: ShellCheck y formato shfmt.
- Zsh, Lua y Python: sintaxis, incluidos scripts sin extensión y archivos ocultos.
- Datos: JSON, JSONC, TOML y YAML.
- Enlaces: fuentes y destinos del manifiesto, propietarios, duplicados y archivos
  administrados que no estén declarados.
- Documentación Markdown: enlaces a archivos locales existentes.
- Regresiones: instalación selectiva y respaldos en homes temporales, monitores,
  barra, Bluetooth, micrófono, contenedores, Flutter y papelera de Neovim.
- Git: whitespace en cambios preparados y sin preparar.

El descubrimiento respeta `.gitignore` y omite metadatos del editor, cachés,
archivos borrados y datos privados. Las pruebas no reinstalan el host ni crean
contenedores; los casos de audio usan datos sintéticos y objetos simulados.
La integración del explorador de Neovim requiere Snacks instalado por el módulo
Neovim. No descarga plugins para hacer pasar una prueba: si faltan, informa el fallo.

Los validadores leen fuentes; las pruebas usan directorios temporales y pueden
crear cachés de sus runtimes. No cambian perfiles de voz ni capturan el micrófono.
Para aplicar únicamente el formato de un Bash:

```bash
shfmt --write --indent 4 --case-indent RUTA
```

## Límites

Una comprobación correcta no demuestra el arranque de SDDM, permisos de hardware,
calidad audible, interacción gráfica, descargas externas ni instalación limpia.
Complementa con `dotfiles-doctor`, uso real de cada función, un arranque guardando
antes el trabajo y una instalación nueva en VM. Windows necesita su propia prueba
con Winget y PowerShell.

## Fuentes

[`check.sh`](../check.sh), [`setup/validate.py`](../setup/validate.py),
[`tests/run.py`](../tests/run.py) y el
[instalador](../setup/modules/quality.sh).
