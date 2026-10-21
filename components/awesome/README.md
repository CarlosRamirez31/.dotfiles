# AwesomeWM

Sesión X11 nativa para VMware con Awesome 4.3, Wibar, Naughty y Picom oficial.
Instala con `./install.sh awesome`; la instalación completa la incluye por defecto.
Selecciona **Awesome** en SDDM después de reiniciar.
Comprueba la configuración antes de entrar con `awesome -k -c ~/.config/awesome/rc.lua`.

El teclado inicia en **US**. Usa `Super+Space` (tecla Windows+Espacio) o haz clic en el indicador `us`/`latam` de la barra para alternar a **Español Latinoamericano** (`latam`) y volver a US.

Consulta la lista completa y categorizada en [ATAJOS.md](ATAJOS.md).

El emulador Android conserva el mosaico y muestra transparente el espacio sobrante alrededor de su pantalla. Su barra de controles sigue el área visible del dispositivo al moverlo, redimensionarlo o cambiarlo de tag; se coloca a la izquierda si no cabe a la derecha y se mantiene dentro del monitor. El panel de los tres puntos (Extended Controls) abre flotante, sin modificar el reparto del mosaico.

En **Super+P**, arrastrar un monitor dentro de una fila reordena los demás sin
dejar huecos. Para otras distribuciones, los bordes deben tocarse; el panel
rechaza huecos y superposiciones parciales antes de cambiar las salidas.
**Aplicar** muestra una confirmación dentro del panel y permite seguir usando
las otras pantallas. Si no pulsas **Conservar** en 20 segundos, se restaura la
configuración anterior y se actualizan los controles con el estado real.

Puedes ajustar la altura relativa de los monitores para alinear el paso del
mouse. Los desniveles pequeños se conservan al arrastrar. Awesome calcula el
espacio reservado por Polybar desde el borde de cada monitor, de modo que bajar
una pantalla no añada un margen superior extra ni comprima las ventanas.

Con el panel integrado y dos monitores externos, el cambio de distribución
reactiva ambas salidas externas juntas y reconstruye el framebuffer antes de
encenderlas. La restauración utiliza el mismo procedimiento, conserva la
frecuencia actual si no cambia la resolución e intenta mantener las ventanas
en su monitor y tag. Durante el cambio las pantallas externas parpadean.
El botón **Recuperar imagen de los monitores** y `dotfiles-display --recover`
repiten esta recuperación sin guardar otra distribución.

## Escritorios y consumo

La lista de escritorios de Polybar se publica desde las señales de Awesome.
La barra espera cambios del archivo por monitor mediante inotify, sin lanzar
`awesome-client` cada 0,3 segundos. Los clics siguen seleccionando el escritorio
de la pantalla correspondiente.
El indicador del micrófono también escucha cambios de audio mediante
`pactl subscribe`, actualizando grabación y mute sin arrancar Python cada dos
segundos. Si la conexión de audio termina, Polybar reintenta después de cinco
segundos.

## Tapa de la laptop

En **Super+P → Tapa y energía…** puedes elegir qué hacer con batería, corriente
y monitores externos. El menú muestra la configuración del sistema y permite
guardarla mediante un diálogo de contraseña de administración, sin terminal.
La opción «Usar solo los monitores externos con la tapa cerrada» está activada
por defecto. Con la tapa cerrada y pantallas externas conectadas,
se desactiva el panel integrado; dos monitores externos quedan como dos pantallas
activas. Al abrir la tapa se vuelve a habilitar el panel integrado. La detección
puede tardar hasta cinco segundos y queda pausada mientras el panel de pantallas
está abierto. Sin monitores externos no se desactiva la única pantalla.
La comprobación periódica lee los estados de conexión del kernel y la tapa;
si no cambian, no ejecuta XRandR. Si cambian, usa `xrandr --current`, sin sondear
el hardware para evitar despertar la GPU dedicada cada cinco segundos.
Al detectar un cambio, apaga las salidas desconectadas que todavía conservan
una resolución activa antes de restaurar la distribución de las conectadas.
Abrir **Super+P** o usar
`dotfiles-display --recover` fuerza una consulta completa si Xorg no ha recibido
el cambio de conexión.

Para elegir la acción del sistema al cerrar la tapa, ejecuta en una terminal:

```bash
dotfiles-display --lid-policy suspend suspend ignore
```

Los tres valores corresponden a **batería**, **corriente** y **monitores externos**,
en ese orden. Acepta `ignore` (seguir funcionando), `suspend`, `hibernate`, `lock`
y `poweroff`. La hibernación requiere que el sistema ya esté preparado para ella.
El comando solicita la contraseña de sudo para escribir
`/etc/systemd/logind.conf.d/90-dotfiles-lid.conf` y recarga logind sin cerrar la
sesión. La política recomendada suspende sin monitores y permite trabajar con
ellos aunque la tapa esté cerrada. La opción de Super+P controla las pantallas;
la política de logind controla suspensión, bloqueo o apagado.
