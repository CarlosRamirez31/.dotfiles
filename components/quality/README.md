# Quality

Este componente instala los validadores utilizados por `./check.sh`. Está
separado del escritorio porque sus paquetes existen para desarrollar y mantener
el repositorio, no para ejecutar el escritorio.

## Herramientas

| Paquete | Validación |
| --- | --- |
| `shellcheck` | Errores semánticos, quoting y casos límite en Bash. |
| `shfmt` | Formato reproducible de los scripts Bash. |
| `zsh` | Sintaxis de `.zshrc`, `.zshenv` y módulos `.zsh`. |
| `jq` | Sintaxis de archivos JSON estrictos. |
| `lua` | Sintaxis de la configuración de Awesome y Neovim. |

## Uso

```bash
./install.sh quality
./check.sh
```

El comando descubre los archivos dentro del repositorio, incluyendo rutas
ocultas como `.local/bin`. Ejecuta todas las familias de validaciones aunque una
falle y devuelve código `1` al final si encontró algún problema. Los JSON con
comentarios (`.jsonc`) quedan fuera de `jq` porque no son JSON estricto.

`check.sh` no modifica archivos. Para aplicar el formato Bash esperado:

```bash
shfmt --write --indent 4 --case-indent RUTA
```

La comprobación `git diff --check` también detecta espacios finales y conflictos
de whitespace en cambios todavía no confirmados.
