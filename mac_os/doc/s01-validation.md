# S01 — Validación de ciclo de vida, fallos y distribución

Fecha: 20 de octubre de 2026. Equipo macOS 27.0.1 arm64; BlackHole 2ch 0.7.1.
Bundle de desarrollo construido antes de esta prueba, correspondiente a `5f0b0d6`.
Las pruebas nuevas de fallos controlados se ejecutan sobre el código de esta entrega.

## T002: salida durante registro y caída durante captura

Se inició «Prueba T002 cancelada» y se salió con ⌘Q cuando la UI mostraba
«Habla durante 10 segundos». Al reabrir, la operación
`20e1f1ac-665e-48ad-acca-1efd63592f96` estaba cancelada. No apareció una voz nueva;
«Voz anterior» siguió siendo la única voz y la predeterminada.
No quedaron host, servicio ni worker propios después de salir.

Se inició captura real hacia BlackHole, operación
`5ca5053d-0bb6-44ec-9c7a-8d84a34c7ac7`, y se envió SIGKILL exclusivamente al
servicio identificado por ruta y PID. BlackHole pasó de activo a inactivo.
La UI indicó servicio desconectado e instrucciones de reabrir. Después de reabrir:
servicio conectado, operación interrumpida por reinicio y captura sin reanudación.
Una sesión nueva `b643880b-0bd3-411a-9726-fc558e49173a` pudo iniciarse y cancelarse.

El indicador global del micrófono integrado permaneció activo: el sondeo CoreAudio
por proceso identificó un proceso de Brave que ya lo usaba. No se detuvo ni modificó
ese proceso. La liberación de nuestra captura se acredita por desaparición del
servicio/worker y ausencia de IO de la app, no por exigir que se detengan otras apps.
El sondeo también observó actividad de CoreSpeech en los altavoces.

## T003: fallos controlados y límite físico

Las pruebas del módulo audio ejercitan el mismo selector de formato, recepción de
frames y comprobación de fallos usados por el adaptador:

- Rechazo de PCM I16, 44.1 kHz, cero canales, seis canales y lista vacía.
- Selección de float32 mono/estéreo a 48 kHz dentro del rango soportado.
- Señal de fallo de entrada: no consumir audio pendiente tras el fallo; cancelación
  puede terminar la espera.
- Señal de fallo de salida y cola llena: códigos distintos, sin sobrescribir el frame previo.
- Persistencia SQLCipher de errores y eventos terminales; nuevo trabajo aceptable
  después del fallo, sin reanudar trabajos fallidos tras abrir el journal.

Son fallos inyectados y capacidades sintéticas, no desconexiones de hardware.
El usuario confirmó que no dispone de micrófono USB y pidió continuar con fallos
controlados dejando el ensayo físico pendiente. No se reinició CoreAudio ni se
desinstaló BlackHole para provocar un fallo que afectara a otras aplicaciones.

Durante la preparación/compilación, la sesión real
`01976663-40b7-4216-84a6-f8c9a5f57833` falló con el código de sobrecarga/pérdida de
entrada. La UI mostró el fallo y volvió a permitir administrar voces; el sondeo no
mostró IO del servicio. El código agrupa ambas causas: no se atribuye este resultado
a una desconexión física. Una repetición de la matriz coincidió con ese fallo;
no acredita productor activo durante todo el ensayo. El runner exige ahora ese
estado en cada etapa y falla si no puede demostrarlo.

La repetición con el runner corregido rechazó el ensayo al inicio porque el
productor ya no estaba activo. La UI confirmó otro fallo de sobrecarga/pérdida
(`7921ec1d-85dc-4d92-b20c-dd6d7084651e`). No se cuenta esa ejecución como matriz
aprobada. La primera observación manual con productor activo sigue siendo evidencia
parcial; falta una repetición automatizada estable y la matriz de clientes reales.

Después de terminar cargo test y Clippy se repitió una vez más: sesión
`df4c7f3a-b92a-452c-ab5f-30cae53eb467`, mismo fallo visible, sin IO del servicio al
terminar. El runner rechazó de nuevo la etapa inicial por productor inactivo.
No se puede atribuir el fallo exclusivamente a la compilación; la carga del sistema
seguía siendo aproximadamente 9.94 de media a un minuto. Investigar la causa exacta
antes de aceptar estabilidad: el código público agrupa cola llena y error del
callback. No se modificó ese contrato para hacer pasar las pruebas.

## T004: señal observable y límites

El sondeo de solo lectura está en
`src-tauri/src/modules/audio/test/probes/processes.c`. Usa
`kAudioHardwarePropertyProcessObjectList`, flags de IO y listas de dispositivos por
scope. La matriz opt-in puede repetirse con:

```sh
pnpm test audio-consumers --producer-pid <PID-del-servicio> --device-id <ID-CoreAudio-BlackHole>
```

Los identificadores son de la ejecución actual: no fijarlos en configuración del
producto. El runner requiere herramientas de desarrollo y FFmpeg solo para este
ensayo; no forma parte del runtime distribuido. Los consumidores escriben a un
sumidero, sin guardar PCM. El script termina únicamente los procesos que crea.

Prueba real inicial con productor activo y dos procesos FFmpeg:

| Estado                      | Consumidores observados, excluido el productor |
| --------------------------- | ---------------------------------------------- |
| Productor solo              | 0                                              |
| Primer receptor abierto     | 1                                              |
| Segundo receptor abierto    | 2                                              |
| SIGKILL del primer receptor | 1                                              |
| Cierre del segundo receptor | 0                                              |

Hallazgo relevante: el productor también aparece con BlackHole en su lista de
entradas, aunque su entrada real es el micrófono integrado. Los receptores también
listan BlackHole en el scope de salida, con el flag de salida apagado. Por tanto,
ni `DeviceIsRunningSomewhere` ni pertenecer a una lista de dispositivos prueban
por sí solos que un proceso esté leyendo ese dispositivo.

Excluir el PID propio funciona en la matriz medida. Un proceso externo con IO
simultáneo en varios dispositivos podría seguir siendo ambiguo. Dos pestañas
pueden compartir proceso: contar PIDs no equivale a contar sesiones. No se ha
validado aún esa matriz de navegador ni todos los clientes de llamadas.

El código de BlackHole 0.7.1 incrementa un contador global en `StartIO` y lo reduce
en `StopIO`, sin usar `inClientID`; la propiedad de ejecución expone un booleano.
No se encontró en esa implementación un contrato público de número de lectores
separado del productor. Fuente:
[BlackHole.c v0.7.1](https://github.com/ExistentialAudio/BlackHole/blob/v0.7.1/BlackHole/BlackHole.c).

**Decisión del spike:** señal parcial útil para diagnóstico, todavía insuficiente
para prometer F12. No implementar activación automática con este contador como
si fuera fiable. Evaluar un contrato explícito de lectores en un driver propio y
probar pestañas, múltiples clientes y caídas antes de aprobar T018.

### Dirección aprobada después del hallazgo

El usuario autorizó investigar un driver propio GPLv3, conservando BlackHole para
desarrollo. La fuente 0.7.1 permite configurar dos dispositivos con direcciones
distintas: principal solo entrada, secundario solo salida. En ese diseño la app
escribe en el secundario y los clientes leen el principal; el productor no suma al
contador del principal. Se verificó compilación sintáctica con esos flags y una
prueba en proceso contra las funciones reales `StartIO`/`StopIO`: productor activo
y lectores 0 → 1 → 2 → 1 → 0 mantuvieron contadores separados.

Ese ensayo no carga un driver en CoreAudio. Sigue pendiente verificar IO real,
cierre abrupto de clientes, pestañas, reset del servidor de audio y entrega de
notificaciones de cambios. No se instaló ni se reemplazó ningún driver.
La interfaz futura debería exponer snapshot versionado de actividad de lectores
y un estado desconocido ante error. El servicio hará una lectura inicial y una
relectura al recibir notificaciones; no usará eventos de negocio por bloque PCM.
El adaptador se seleccionará por capacidad/UID, no por el nombre comercial.

| Alternativa                             | Coste y límite para decidir                                                                              |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| CoreAudio + BlackHole externo           | Menos mantenimiento propio, pero la señal medida es ambigua; no aprueba F12                              |
| Driver GPLv3 con dispositivos separados | Requiere mantener HAL, identidad, distribución, avisos, firma y matriz de clientes; dirección autorizada |
| Acuerdo con proveedor                   | Coste por cotizar y contrato explícito; no se ha contratado ni solicitado en nombre del usuario          |

La prueba reproducible de contadores es `pnpm test driver-spike --source <BlackHole.c>`.
Se debe comprobar en el prototipo instalado la notificación de inicio/fin, no solo
el contador leído manualmente; el código upstream inspeccionado no demuestra esa
entrega. También se debe medir el primer bloque útil con modelos preparados y el
tratamiento del estado desconocido, sin confundir silencio con ausencia de lectores.

## T020: decisión de licencia y límites del paquete actual

El usuario eligió código abierto compatible con GPLv3 para la app local. Esta
decisión no relicencia automáticamente los demás directorios del repositorio.

La [licencia de BlackHole 0.7.1](https://github.com/ExistentialAudio/BlackHole/blob/v0.7.1/LICENSE)
distingue código GPLv3 de binarios oficiales y marca. La ruta propuesta es compilar
desde fuente, con nombre/identificadores/recursos propios y cumplimiento GPLv3,
o conseguir permiso explícito para redistribuir el instalador oficial. No se
reempaca el instalador oficial por el mero hecho de elegir GPLv3. El driver
preexistente continúa siendo una dependencia externa y se preserva.

El bundle actual incluye siete recursos fuente/manifiesto; no contiene Python,
PyTorch, pesos ni driver. Firma observada: ad hoc, sin TeamIdentifier ni recursos
sellados. No se presenta como instalador firmado, notarizado o listo para otro Mac.

El venv de desarrollo apunta a `/opt/homebrew/opt/python@3.14/bin`; copiar ese venv
solo no produce un runtime autónomo. Inventario de metadatos de sus 27 paquetes:
[runtime-license-inventory.json](runtime-license-inventory.json). Es evidencia de
versiones instaladas, no aprobación legal automática de todas las dependencias.

| Componente                  | Versión / artefacto                                     | Licencia o evidencia                                                              |
| --------------------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Reducción de ruido          | nnnoiseless 0.5.2, implementación Rust usada por la app | BSD-3-Clause en Cargo metadata; conservar avisos de código/modelo                 |
| nomo-pvad                   | `cb828468d183424fd574984f00b3ffbcce0be9bc`              | Apache-2.0 y THIRD_PARTY_NOTICES fijados en manifiesto                            |
| Peso nomo                   | 36 576 677 bytes                                        | El upstream declara Apache-2.0; falta incluir WEIGHTS_LICENSE en el paquete final |
| ERes2NetV2                  | 71 768 231 bytes                                        | Atribución Apache-2.0 en upstream; SHA-256 fijado, URL todavía usa master         |
| PyTorch / torchaudio        | 2.11.0 / 2.11.0                                         | Revisar y conservar licencias transitivas y bibliotecas incluidas                 |
| Python standalone candidato | CPython 3.14.7, release 20260924, arm64                 | PSF y avisos de dependencias del artefacto; origen oficial Astral                 |
| Driver de desarrollo        | BlackHole 2ch 0.7.1                                     | GPLv3 para fuente; restricciones diferenciadas para binarios y marca              |

Archivo oficial de Python descargado: 26 781 712 bytes, SHA-256
`d3da099bb2bdd57e2f5ff8496cb9827f7d92eee332b09f8dc93706dabfc51a96`, coincidente con
el digest de la API de GitHub. Fuente:
[release 20260924](https://github.com/astral-sh/python-build-standalone/releases/tag/20260924).
Se extrajo en un directorio temporal y se trasladaron las dependencias instaladas
y modelos de desarrollo a ese árbol. Con PATH reducido, Python en modo aislado y
un sandbox que deniega red, Homebrew, SDK, Rust y `.runtime` original, el worker
real extrajo un embedding y procesó 35 bloques de las muestras públicas upstream.
Resultado: probabilidades entre 0.04047 y 0.88846. El ejecutable y `sys.prefix`
resolvieron al directorio temporal, con Python 3.14.7 y PyTorch 2.11.0.

Esto demuestra relocación/autonomía del prototipo; copiar site-packages no es el
build reproducible de release. Todavía deben instalarse wheels verificados en el
staging con el lockfile, retirar herramientas de desarrollo y conservar los avisos.
La prueba no equivale a instalación en otro Mac limpio ni a validación de firma.

Tamaño del árbol temporal completo: aproximadamente 836 MiB en disco, con modelos,
intérprete y dependencias de desarrollo aún sin recortar. No es tamaño final de
descarga ni del instalador. `otool -L` del intérprete mostró dependencias del sistema
macOS, sin rutas Homebrew; la ejecución aislada verificó las bibliotecas cargadas
por el recorrido de registro/inferencia. El artefacto candidato queda fijado en
`runtime/personal-voice/portable-python.json`.

En esta ejecución bajo carga, mediana de inferencia 866.98 ms y máximo 3093.06 ms
por bloque de 160 ms. **No aprueba tiempo real**. Separar autonomía del runtime de
calidad/latencia; repetir benchmark con carga controlada y presupuesto de recursos
antes de aceptar voz personal. No se usaron muestras de voz del usuario.

Puertas pendientes: suministro reproducible desde wheels con hashes, avisos
completos de todas las dependencias, runtime probado sin herramientas globales,
driver con identidad/distribución resueltas, firma/notarización y otro Mac limpio.
No se requiere implementar el instalador S06 para investigar S01, pero sí demostrar
una ruta de distribución viable antes de cerrar el sprint.

## Verificaciones de esta entrega

- Rust: 42 pruebas aprobadas, 0 fallos, 1 prueba de modelo omitida en la suite normal.
  El modelo real se ejercitó por separado con el runtime trasladado y aislado.
- Clippy `--all-targets -- -D warnings`, rustfmt, ESLint del runner, Ruff,
  clang-format y Prettier de archivos afectados aprobados.
- Sondeo C compilado con `-Wall -Wextra -Werror`; prueba de contadores del driver aprobada.
- Matriz automatizada de consumidores **no aprobada**: productor inactivo por fallo
  real de captura. La observación manual previa 0/1/2/1/0 es evidencia parcial.
- App final abierta sin captura propia; BlackHole inactivo. La captura ajena se preservó.

No se generó un nuevo instalador ni se publicaron binarios o commits. S01 permanece
abierto por estabilidad de audio, validación real del driver y preparación de distribución.
