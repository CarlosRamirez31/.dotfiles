# Apariencia

Abre **Apariencia** desde el panel principal, el lanzador de aplicaciones o
`dotfiles-appearance`. Usa Awesome, Picom y GTK 3, sin nuevas dependencias.
Su interfaz usa tipografía monoespaciada, pestañas y colores sobre fondo oscuro,
con un estilo de terminal.

| Control | Rango |
| --- | --- |
| Separación | 0–100 px |
| Bordes | 0–20 px |
| Esquinas | 0–99 px |
| Tamaño de sombra | 0–100 px |
| Intensidad de sombra | 0–100% |
| Opacidad inactiva | 0–100% (0 oculta las ventanas inactivas) |
| Color activo | Cualquier color RGB |
| Duración de animación | 80–500 ms |
| Duración por evento | 0–500 ms (0 usa la duración general) |
| Intensidad de desenfoque | 1–20 |
| Opacidad de menús y paneles | 50–100% |

- Ventanas: separación, grosor de bordes y color de la ventana activa.
- Efectos: esquinas, sombras, tamaño e intensidad de sombra y desvanecimiento.
- Animaciones: interruptores independientes para animar apertura/cierre de
  ventanas, menús/paneles y ocultar/mostrar ventanas. Estilos: Zoom suave, Zoom
  amplio, Zoom inverso, Deslizamiento, Vuelo y Desvanecimiento. Requiere Picom 13
  o posterior.
- Desenfoque Dual Kawase: interruptor e intensidad. Solo se aprecia detrás de
  superficies transparentes; puedes bajar la opacidad de menús y paneles en
  Transparencia. Polybar, el emulador y las ventanas de bloqueo quedan
  excluidos de estos efectos nuevos, al igual que las ventanas a pantalla completa.
- Transparencia: opacidad de ventanas inactivas; las aplicaciones conservan su
  configuración interna de transparencia.
- Fondo: acceso al selector existente. El fondo se guarda desde ese selector,
  independientemente de las pruebas de efectos.

Los controles actualizan una muestra local. **Probar 20 s** aplica los ajustes
al escritorio temporalmente. **Guardar** los conserva y **Cancelar** revierte
la prueba. Si no guardas, un proceso independiente restaura la configuración
anterior al terminar los 20 segundos, incluso si se cierra el editor por un fallo.
Cerrar normalmente durante una prueba también la revierte.

**Restaurar valores** carga los valores originales de este escritorio en los
controles; requiere Probar o Guardar para aplicarlos. Los perfiles Equilibrado,
Suave y Sin efectos también se pueden modificar antes de aplicarlos.

Todos los efectos nuevos vienen **desactivados**, también al leer preferencias
guardadas antes de esta actualización. Los perfiles existentes tampoco los
activan. La opacidad de menús empieza en 100%; se conservan los ajustes antiguos
de sombras, esquinas y desvanecimiento. Abrir el editor o mover un control no
aplica cambios al escritorio: usa **Probar 20 s** o **Guardar**. La muestra local
representa la geometría anterior; las animaciones y el desenfoque se comprueban
con Probar. No hace falta reiniciar Awesome ni instalar otro compositor.

En **Animaciones**, despliega **Al abrir**, **Al cerrar**, **Al restaurar** o
**Al ocultar** para elegir un tipo, lado y duración independientes. Por defecto
cada evento usa el estilo y la duración generales, conservando las preferencias
anteriores. **Sin animación** elimina también el desvanecimiento de ese evento,
si su interruptor de animaciones está activo. Los ajustes por evento se comparten
entre las ventanas y los menús que tengan sus animaciones activadas.

En Deslizamiento y Vuelo, el lado indica **desde dónde entra** al abrir/restaurar
y **hacia dónde sale** al cerrar/ocultar. Por ejemplo: Al abrir → Vuelo →
Izquierda → 300 ms; Al cerrar → Desvanecimiento → 150 ms. Deslizamiento revela
la ventana dentro de su área; Vuelo la desplaza desde/hacia fuera de la pantalla.
Zoom inverso empieza más grande al entrar y aumenta el tamaño al salir.

Los efectos usan los [presets de Picom 13](https://github.com/yshui/picom/blob/v13/data/animation_presets.conf).

Ocultar/mostrar anima los eventos `show`/`hide` de Picom (por ejemplo minimizar
y restaurar). Solo afecta a cambios de espacio si Awesome genera esos eventos;
no implementa un deslizamiento del escritorio completo ni anima mover o
redimensionar ventanas. Los menús son ventanas de tipo menú/tooltip y los
diálogos de Awesome, incluidos los paneles de música y sistema.

Los ajustes se guardan en `~/.config/dotfiles/appearance.json` (respeta
`XDG_CONFIG_HOME`). No modifica los archivos versionados del tema ni de Picom.
La configuración de Picom se genera a partir de su archivo base, conservando
backend, sincronización y exclusiones. Al cambiar efectos se reinicia Picom;
puede haber un breve parpadeo. Cambiar solo bordes, espacios o color no lo reinicia.
Las ventanas especiales del escritorio y el emulador conservan sus bordes propios.

Al activar animaciones, el editor convierte las exclusiones del archivo base a
reglas de Picom 13 en el archivo temporal, conservando la opacidad propia de las
aplicaciones. Con las animaciones apagadas mantiene el formato anterior.
Si añades manualmente `rules`, `animations`, `wintypes` u `opacity-rule` a la base,
la activación de animaciones se rechaza con un aviso para no sobrescribir esas
reglas personalizadas. La base versionada no se modifica.

Al iniciar sesión se leen las preferencias guardadas, sin reutilizar una prueba
temporal de una sesión anterior. Primero se configura la pantalla y se restaura
el fondo; después arranca Picom con GLX para evitar que lea un fondo aún sin
preparar. No se cambia automáticamente a otro backend.
Awesome comprueba Picom cada cinco segundos y
lo recupera si se cierra inesperadamente; no lo reinicia mientras está funcionando
ni interfiere con una operación de Guardar o Probar en curso. Los archivos
temporales, el registro de Picom y el estado de las pruebas están en
`$XDG_RUNTIME_DIR/dotfiles-appearance/`.

```bash
dotfiles-appearance --export
dotfiles-appearance --export-saved
python3 -B -m unittest discover -s tests/appearance
lua tests/appearance/test_appearance.lua
```

Fuentes: [editor](../bin/dotfiles-appearance),
[integración Awesome](../config/awesome/appearance.lua),
[Picom base](../config/picom/picom.conf).

Las pruebas ejercitan los controles y señales GTK sin mostrar una ventana ni
cambiar el escritorio; esa parte se omite si no hay un display X11 disponible.
También verifican persistencia, límites, perfiles, cancelación, cierre y la
reversión independiente de una prueba sin confirmar.

## Avatar de inicio de sesión

La pestaña **Avatar** contiene los 61 estilos del catálogo DiceBear incluido,
con miniaturas, búsqueda, personajes aleatorios y opciones propias
de cada estilo. El personaje queda fijo a la izquierda mientras se recorre el
catálogo o se personalizan sus partes. Cabello, ojos y accesorios se eligen
mediante miniaturas; los colores tienen su selector visual. El selector de partes
usa búsqueda y una lista de altura limitada con desplazamiento interno.
Las pestañas conservan su tamaño y se recorren con los botones ‹ y ›. Funciona sin conexión. **Choose photo** abre tu selector de
archivos y permite encuadrar una foto mediante zoom y posición. El original se
conserva. **Save favorite** guarda una copia PNG en
`~/.local/share/dotfiles/avatar/favorites/`; **Open favorite** permite reutilizarla.

**Guardar**, estando en Avatar, conserva el personaje
editado y aplica la imagen estática al usuario actual. El estilo, sus opciones
y la foto seleccionada se restauran al volver a abrir el editor. Polkit pide
administración mediante el agente gráfico `polkit-gnome` para copiarla a `/usr/share/sddm/faces/USUARIO.face.icon`, legible
por SDDM incluso cuando el directorio personal es privado. La atribución del
estilo se muestra en el editor y se conserva en los metadatos del PNG.
En las otras pestañas, Guardar/Probar controlan los efectos del escritorio.
En Avatar se desactivan Probar y Restaurar valores para evitar confusiones.

El catálogo está fijado en `@dicebear/styles 10.6.0` y el motor en
`@dicebear/core 10.7.0`. Se incluyen solo sus archivos de ejecución y licencias
originales (aproximadamente 3,4 MB); no se instala npm ni se descargan estilos al
abrir el editor. Fuentes: [motor](https://github.com/dicebear/dicebear) y
[estilos](https://github.com/dicebear/styles). Las licencias específicas se
incluyen en cada definición y en `share/avatar/vendor/styles/LICENSE`.
