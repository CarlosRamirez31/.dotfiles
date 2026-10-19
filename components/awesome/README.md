# AwesomeWM

Sesión X11 nativa para VMware con Awesome 4.3, Wibar, Naughty y Picom oficial.
Instala con `./install.sh awesome`; la instalación completa la incluye por defecto.
Selecciona **Awesome** en SDDM después de reiniciar.
Comprueba la configuración antes de entrar con `awesome -k -c ~/.config/awesome/rc.lua`.

El teclado inicia en **US**. Usa `Super+K` (tecla Windows+K) o haz clic en el indicador `us`/`latam` de la barra para alternar a **Español Latinoamericano** (`latam`) y volver a US.

Consulta la lista completa y categorizada en [ATAJOS.md](ATAJOS.md).

En **Super+P**, arrastrar un monitor dentro de una fila reordena los demás sin
dejar huecos. Para otras distribuciones, los bordes deben tocarse; el panel
rechaza huecos y superposiciones parciales antes de cambiar las salidas.
**Aplicar** muestra una confirmación dentro del panel y permite seguir usando
las otras pantallas. Si no pulsas **Conservar** en 20 segundos, se restaura la
configuración anterior y se actualizan los controles con el estado real.

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
