# SDDM

Este componente aplica SilentSDDM como tema de la pantalla de inicio. Forma
parte de la instalación completa, inmediatamente después de `system`, por lo
que `./install.sh` deja SDDM listo para el siguiente arranque.

Incluye una copia local de SilentSDDM, por lo que el instalador no descarga el
tema ni necesita un clon previo en `~/Projects`. Instala las dependencias Qt,
selecciona la variante Catppuccin Mocha, configura el teclado virtual y
registra las fuentes que usa el tema.

## Instalación y comprobación

```bash
./install.sh sddm
sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/silent
```

El cambio se aplica al próximo reinicio o al iniciar SDDM de nuevo; el
instalador nunca termina la sesión gráfica actual.

## Archivos administrados

| Ruta | Función |
| --- | --- |
| `/usr/share/sddm/themes/silent` | Tema SilentSDDM incluido en este repositorio. |
| `/usr/share/fonts/silent-sddm` | Fuentes del tema. |
| `/etc/sddm.conf.d/10-silent.conf` | Activa el tema y el teclado virtual de Qt. |

La copia incluida procede de
[uiriansan/SilentSDDM](https://github.com/uiriansan/SilentSDDM), bajo GPL-3.0;
la licencia original está en `system/sddm/theme/LICENSE`.

## Fuentes del módulo

Instalador: [`setup/modules/sddm.sh`](../setup/modules/sddm.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
