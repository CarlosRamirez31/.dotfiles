# Spike del driver Local

Investigación autorizada: driver propio compatible con GPLv3, con identidad propia.
BlackHole instalado permanece como dependencia externa de desarrollo.

La fuente de prueba es [BlackHole 0.7.1](https://github.com/ExistentialAudio/BlackHole/blob/v0.7.1/BlackHole/BlackHole.c).
El runner comprueba SHA-256 antes de compilar. No descarga, instala ni modifica un
driver; compila un ejecutable temporal que ejercita los contadores internos.

```sh
pnpm test driver-spike --source /ruta/a/BlackHole.c
```

Hipótesis: dispositivo principal público solo de entrada, dispositivo secundario
solo de salida. Los lectores arrancan IO en el principal y el productor escribe
en el secundario. El test mantiene el productor activo mientras los lectores
pasan por 0 → 1 → 2 → 1 → 0, y comprueba que los contadores no se mezclan.

Esto no demuestra cómo CoreAudio entrega StartIO/StopIO ante pestañas, caídas o
reconfiguración. Tampoco valida notificaciones ni el transporte real entre ambos
dispositivos. Antes de implementar F12 se necesita un prototipo HAL instalado y
esa matriz real, con salida segura ante estado desconocido. No cambiar la entrada
predeterminada del sistema durante el ensayo.

La distribución final requiere nombre, bundle ID, UIDs y recursos propios,
avisos GPLv3 y fuentes correspondientes. Los instaladores oficiales y marcas del
proveedor no se redistribuyen automáticamente por este test. Ver
[evidencia y decisiones S01](../../doc/s01-validation.md).
