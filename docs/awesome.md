# AwesomeWM

Sesión X11 con AwesomeWM, Polybar, notificaciones Naughty y Picom. Funciona en hardware físico y en VMs con soporte X11.
Instala con `./install.sh awesome`; la instalación completa la incluye por defecto.
Selecciona **Awesome** en SDDM después de reiniciar.
Comprueba la configuración antes de entrar con `awesome -k -c ~/.config/awesome/rc.lua`.

El teclado inicia en **US**. Usa `Super+Space` (tecla Windows+Espacio) o haz clic en el indicador `us`/`latam` de la barra para alternar a **Español Latinoamericano** (`latam`) y volver a US.

Consulta la lista completa y categorizada en [lista de atajos](awesome-atajos.md).

Las aplicaciones normales en mosaico se ajustan al espacio asignado aunque
declaren un tamaño mínimo mayor, para evitar que invadan el monitor vecino.
Si una aplicación queda demasiado estrecha para mostrar sus controles, amplía
su columna o pásala a flotante con `Alt+V`. Los diálogos y el emulador Android
conservan sus restricciones especiales de tamaño.

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

Las resoluciones y frecuencias se consultan por salida con XRandR. Cada fila
incluye un selector de Hz para la resolución elegida; se conserva la frecuencia
seleccionada al aplicar y guardar. «Máxima» indica la mayor resolución ofrecida
por esa conexión y «Preferida» el modo recomendado por el monitor/controlador.
Los perfiles incluyen la identidad EDID para no reutilizar los ajustes de otro
monitor conectado al mismo puerto. Al cambiar la conexión se vuelve a consultar
el hardware; las comprobaciones periódicas sin cambios no sondean la GPU.
`dotfiles-display --status` muestra los modos, Hz e identidad detectados en JSON.

Windows + P muestra «Activo ahora» con la resolución y frecuencia que está
usando cada salida, separado de los selectores de cambios pendientes. Se
actualiza al enfocar la ventana, con «Actualizar estado real» y después de
aplicar. Antes de conservar el cambio se verifican los modos activos; si el
controlador mantiene otra resolución o frecuencia, se restaura el estado anterior.

En **Windows + P**, selecciona una pantalla desde el dibujo o la lista para
editar su resolución, frecuencia, escala de aplicaciones (100–200 %), tamaño
de fuentes (8–32 pt con deslizador) y tamaño de Polybar (75–200 %) por separado. La resolución
y la organización del escritorio permanecen iguales al cambiar estos valores.
Las aplicaciones abiertas desde Awesome reciben ambos ajustes según el monitor
bajo el puntero; vuelve a abrirlas para que los tomen. El deslizador acepta
tamaños de fuente en décimas de punto. El primer nivel de escala
de aplicaciones, 110 %, aplica un aumento efectivo del 20 % para que el cambio
sea visible. El tamaño de fuente adicional ajusta las fuentes de las aplicaciones
compatibles y Alacritty. Polybar usa su selector propio. Algunas aplicaciones
pueden ignorar los ajustes de fuente de X11. Las preferencias se guardan por
EDID en `display-appearance.json`.
Hay 20 segundos para conservar o restaurar la prueba.

La visibilidad de Polybar se controla por proceso y monitor. Una ventana a
pantalla completa solo oculta la barra de su pantalla; las demás siguen visibles.
Acerca el cursor al borde superior durante un momento para mostrarla temporalmente.

## Fuentes del módulo

Instalador: [`setup/modules/awesome.sh`](../setup/modules/awesome.sh). Los archivos y destinos administrados
se declaran por módulo en [`setup/links.tsv`](../setup/links.tsv); las rutas
`.config/` y `.local/` de esta guía se refieren al home instalado.
