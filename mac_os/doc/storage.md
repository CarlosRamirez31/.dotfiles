# Persistencia local

## Propuesta

SQLite embebido es adecuado para ajustes y perfiles por usuario; no requiere un servidor de base de datos. Para cifrar archivos se propone SQLCipher Community, con clave aleatoria guardada en Keychain. SQLite estándar no cifra la base. Confirmar compilación arm64/x64, licencia y rendimiento antes de elegir el binding Rust y añadir dependencias.

No se configura una conexión a una DB externa en Local. Configuración de ubicación y políticas mediante opciones tipadas del adaptador; ruta predeterminada privada bajo `~/Library/Application Support/<bundle-id>/`. Sin selector libre hacia carpetas compartidas o unidades de red durante la beta.

## Propiedad de datos

El servicio es el único dueño de las conexiones. React y el host consultan mediante HTTP al BFF; no abren el archivo. Repositorios por módulo, migraciones propias y nombres delimitados; no consultas cruzadas a tablas ajenas. Commons configura el proveedor, no los repositorios de negocio.

Guardar perfiles de ajustes, perfil activo, metadatos y embeddings de voz cifrados, manifiestos de instalación, versión del esquema y estado recuperable de sagas. Los pesos grandes permanecen como archivos verificables, no como filas. No guardar audio crudo por defecto. Las grabaciones de registro son efímeras; eliminar cualquier temporal también ante error/cancelación.

## Claves y recuperación

Clave fuera de la DB, config, argumentos de proceso y logs. Acceso al Keychain mediante el servicio firmado y una identidad estable; no compartir la clave con React. Keychain bloqueado o permiso denegado deja un estado recuperable. Perder la clave impide abrir el archivo: no crear una base vacía encima ni prometer recuperación sin backup cifrado.

El cifrado en reposo no protege contra procesos que controlan una sesión de usuario desbloqueada ni contra acceso a la memoria del servicio. Backups y exportaciones de perfiles requieren política explícita; no exportar embeddings sensibles en JSON en claro.

## Rendimiento y consistencia

Probar WAL, timeout de bloqueo y una cola de escritura para transacciones cortas. WAL mejora concurrencia, pero sigue habiendo un único escritor; no usarlo como garantía de velocidad. DB, WAL, temporales y backups deben comprobarse como parte del cifrado. Probar con el proveedor elegido antes de activar WAL.

Nada de SQL en el callback de audio. Las modificaciones de perfil se persisten fuera del camino de audio y se aplican como una nueva configuración validada. Migraciones transaccionales, backup previo a cambios destructivos y prohibición de downgrade silencioso. Usar API de backup consistente, no copiar solo el archivo principal mientras está activo.

Fuentes: [SQLCipher Community](https://www.zetetic.net/sqlcipher/community/), [cifrado SQLCipher](https://www.zetetic.net/sqlcipher/about/), [SQLite WAL](https://www.sqlite.org/wal.html), [Keychain](https://developer.apple.com/documentation/security/keychain-services).
