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

- Ventanas: separación, grosor de bordes y color de la ventana activa.
- Efectos: esquinas, sombras, tamaño e intensidad de sombra y desvanecimiento.
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

Los ajustes se guardan en `~/.config/dotfiles/appearance.json` (respeta
`XDG_CONFIG_HOME`). No modifica los archivos versionados del tema ni de Picom.
La configuración de Picom se genera a partir de su archivo base, conservando
backend, sincronización y exclusiones. Al cambiar efectos se reinicia Picom;
puede haber un breve parpadeo. Cambiar solo bordes, espacios o color no lo reinicia.
Las ventanas especiales del escritorio y el emulador conservan sus bordes propios.

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
