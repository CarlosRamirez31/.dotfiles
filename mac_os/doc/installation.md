# Instalación, integración y desinstalación

Estado: especificación para implementar en la edición Local de macOS. Todavía no existe instalador completo, servicio, runtime de IA ni desinstalador. El build actual solo genera el scaffold `.app`.

## Compilar no instala en el equipo

El build prepara los ejecutables, runtimes, recursos y artefactos distribuibles; no instala drivers ni modifica el sistema del desarrollador o del runner. El usuario ejecuta después el instalador firmado. Instalar tampoco arranca automáticamente captura o inferencia: el servicio nace al abrir la aplicación y termina al salir.

## Paquete de distribución Local

Se propone un `.pkg` firmado y notarizado para la experiencia completa en macOS, construido con `pkgbuild`/`productbuild` después de generar el bundle Tauri. Tauri genera `.app` y puede generar `.dmg`; un DMG por sí solo no instala un driver de audio ni resuelve la desinstalación. La creación del PKG será una etapa propia del pipeline.

El paquete contendrá la aplicación de barra de menús, el servicio supervisor de IA como sidecar, las bibliotecas/runtime privados requeridos, los modelos seleccionados cuya redistribución esté aprobada, los avisos de licencia y un auxiliar de mantenimiento/desinstalación firmado. No se instalarán todos los candidatos: RNNoise y DeepFilterNet son alternativas hasta que el benchmark decida.

Objetivo del instalador completo: funcionamiento de las funciones incluidas sin red después de instalar. Para ello también se debe empaquetar el modelo de registro ERes2NetV2 si se distribuye nomo-pvad; su descarga automática original deberá sustituirse por resolución de un recurso local verificado. Si un peso no puede redistribuirse, esa función requerirá descarga explícita en el asistente inicial y no se anunciará como disponible offline desde el instalador.

No se requiere que el usuario tenga Rust, Node, pnpm, Homebrew, Python o PyTorch globales. Si la IA necesita Python/PyTorch, el paquete incluye un runtime aislado por arquitectura, probado y firmado con todas sus bibliotecas. No se ejecuta `pip install` al abrir la app.

### Qué prepara el build

1. Leer un catálogo versionado de modelos y runtimes con URL oficial, commit/release inmutable, hashes, licencia, tamaños y arquitectura. No descargar `latest` en una release.
2. Obtener y verificar artefactos permitidos en un directorio de staging; fallar ante hash incorrecto, licencia pendiente o archivo ausente. El catálogo y sus hashes se revisan con el código.
3. Compilar el servicio y sus módulos para arm64 o x64. Configurar `bundle.externalBin` para los ejecutables y `bundle.resources` para datos estáticos. El runtime Python puede requerir una estructura completa de recursos; `externalBin` por sí solo no empaqueta sus dependencias.
4. Incluir solo pesos necesarios para las funciones habilitadas. Publicar tamaños reales de descarga e instalación; los 35 MB de nomo-pvad no representan el tamaño de toda la app.
5. Firmar auxiliares, runtimes y bibliotecas y después el bundle; construir y firmar PKG con identidad de instalador, notarizar y adjuntar el ticket. Validar en otro Mac limpio.
6. Probar instalación, apertura offline, salida y desinstalación antes de publicar una beta externa.

No se modifica el contenido firmado del `.app` en ejecución. Los modelos originales incluidos pueden leerse desde sus recursos; actualizaciones descargadas se guardan por usuario y versión bajo Application Support. Un resolvedor elige la versión registrada; evita duplicar todos los pesos en el primer inicio.

### Driver virtual

El adaptador identifica si el driver ya existe. Solo puede instalarse como componente del producto cuando se haya resuelto la licencia y el paquete del proveedor permita esa distribución. BlackHole sigue siendo candidato; mientras se instala por separado, la UI lo muestra como dependencia externa, no como parte propiedad de la app.

Instalar o eliminar componentes en `/Library/Audio/Plug-Ins/HAL` requiere el mecanismo autorizado de macOS y puede requerir reinicio o cierre de llamadas. No reiniciar CoreAudio silenciosamente. Un auxiliar privilegiado de mantenimiento tendrá operaciones concretas y rutas fijas; no ejecutará shell libre ni recibirá una ruta arbitraria desde React. Su ejecución será puntual: no se crea un daemon privilegiado permanente para inferencia.

## Integración de cada IA

La UI llama casos de uso mediante HTTP al BFF local; el servicio recibe la sesión y compone procesadores por DI. Cada módulo implementa el puerto de procesamiento, mantiene su estado por sesión y publica eventos de estado/fallo. El audio usa buffers acotados, no JSON ni eventos de negocio por muestra.

- **RNNoise:** biblioteca nativa C integrada en el módulo Rust mediante un adaptador FFI revisado; preparar/resamplear al formato requerido por la versión elegida, mantener estado por stream y liberar al detener. No lanzar un comando externo por cada bloque.
- **DeepFilterNet:** alternativa a evaluar mediante su implementación Rust o un worker privado. Verificar formato, estado de streaming, modelo, coste y latencia. La herramienta de procesar WAV no prueba por sí sola integración en tiempo real.
- **nomo-pvad:** worker privado inicialmente candidato, con los pesos principales y ERes2NetV2 disponibles localmente. Registro de voz → embedding cifrado; stream a 16 kHz → probabilidad cada 160 ms → política de paso/silencio del módulo `personal-voice`. El servicio mantiene el audio alineado con esa decisión. No separa voces superpuestas.
- **Gestor de modelos:** carga diferida, verificación, selección de versión, actualización explícita y eliminación. Cada worker termina con el servicio y nunca sobrevive al host.

El spike fijará los motores, bindings, versiones y hashes antes de implementar el instalador. No se han añadido estas dependencias al proyecto todavía.

## Desinstalar desde la aplicación

Ubicación prevista: Ajustes → Instalación y almacenamiento → Desinstalar. Mostrar los componentes encontrados y ofrecer «Conservar perfiles» o «Eliminar también mis datos». El usuario confirma una operación concreta; cancelar antes de comenzar no cambia nada.

Secuencia del caso de uso `UninstallApplication`:

1. Bloquear nuevas sesiones/actualizaciones, mostrar que las llamadas perderán esta entrada y detener pipeline y workers.
2. Restaurar la entrada predeterminada anterior solo si el producto la cambió, la actual sigue siendo la suya y la anterior todavía existe. No sobrescribir cambios posteriores hechos por el usuario.
3. Preparar un plan persistido y restringido de limpieza con inventario de propiedad, versión e identificador de instalación. Validar rutas canónicas y enlaces simbólicos para no salir de directorios propios.
4. Si se conserva información, mantener DB y clave de Keychain juntas; eliminar la clave haría irrecuperable la DB cifrada. Si se elige borrado completo, eliminar perfiles, embeddings, DB/WAL, modelos descargados, cachés, temporales, logs y únicamente las claves propias.
5. Delegar en un auxiliar firmado que pueda continuar después de salir el host y cerrar el servicio. Ese auxiliar elimina el bundle y componentes propios, deja un resultado visible y termina; su limpieza temporal debe estar probada. No intentar borrar el ejecutable principal mientras coordina su propio cierre.
6. Retirar driver/helper/recibos de instalación únicamente cuando pertenecen a esta instalación y su eliminación está autorizada. Un driver preexistente o compartido se conserva y se informa; la app no borra software de otros productos. Olvidar un recibo PKG no elimina sus archivos.
7. Verificar que no quedan procesos ni archivos propios pendientes; ante denegación de permisos, componente en uso o reinicio pendiente, mostrar resultado parcial y permitir reintento. No mostrar «desinstalación completa» si falta una fase.

«Eliminar todo» significa todo lo instalado por este producto para el usuario y los componentes de sistema de su propiedad. No se borran datos de otras cuentas, copias de respaldo externas ni preferencias de Teams/Zoom/Meet/Slack. La eliminación lógica no promete borrado forense en SSD; no se limpian bases de permisos de macOS mediante comandos no soportados.

El PKG también debe facilitar un acceso al mismo desinstalador si la app no abre. Actualizar/reparar es un flujo separado: conserva datos y no dispara el borrado completo. Añadir inventario, actualización atómica y compensaciones para fallos de instalación; no hay transacción global que deshaga automáticamente todos los cambios del sistema.

## Cloud y Windows futuros

Cloud tendrá también frontend y servicio local en segundo plano, activo solo mientras la app esté abierta. Ese servicio conserva captura, buffers, transporte seguro al BFF, recepción y entrega al micrófono virtual. Las IA se ejecutan detrás de las APIs remotas; Cloud no instala pesos ni runtimes de inferencia locales. Su desinstalador elimina sus propios componentes, preferencias y credenciales, no recursos ni datos en servidores. La configuración por aplicación sigue pendiente de diseñar.

Windows se planificará después: instalador NSIS o MSI de Tauri, desinstalación integrada con el sistema y botón dentro de la app que invoque ese mismo mecanismo. Puertos comunes `InstallationInventory`, `ModelStore` y `UninstallCoordinator`, con adaptadores por plataforma. El driver, almacenamiento de claves, permisos, firma y eliminación de archivos en uso deben implementarse y probarse específicamente en Windows. BlackHole es para macOS y no se trasladará a Windows. No hay build ni soporte Windows en esta etapa.

## Pruebas obligatorias

Instalación limpia y offline; arquitectura incorrecta; espacio insuficiente; cancelación; actualización interrumpida; modelo alterado; driver preexistente; varios usuarios; Keychain denegado; app movida; salida con llamada activa; desinstalación con/sin perfiles; reinicio durante limpieza; reparación y reinstalación. Verificar ausencia de procesos huérfanos y archivos propios, preservación de componentes ajenos y funcionamiento de audio tras restauración. Medir instalación y arranque real, no solo generación de un paquete.

## Documentación oficial

- [Sidecars Tauri](https://v2.tauri.app/develop/sidecar/).
- [Recursos incluidos en Tauri](https://v2.tauri.app/develop/resources/).
- [DMG Tauri](https://v2.tauri.app/distribute/dmg/).
- [Empaquetado macOS de Apple](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution).
- [Notarización Apple](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).
- [Instaladores Windows de Tauri](https://v2.tauri.app/distribute/windows-installer/).
- [PyInstaller: empaquetado de runtimes](https://pyinstaller.org/en/stable/usage.html).
- [BlackHole: instalación, desinstalación y licencia](https://github.com/ExistentialAudio/BlackHole).
