# Voces con nombre y predeterminada

Decisión confirmada el 20 de octubre de 2026: varias voces con nombre; una predeterminada; reemplazar o
eliminar requiere detener primero la captura o el registro. Estos perfiles de voz son distintos de los perfiles
de ajustes de F03. Sin cuentas ni login.

## Experiencia

El inicio muestra primero la voz predeterminada y después las demás. La predeterminada queda seleccionada
al abrir; elegir otra para una sesión no cambia automáticamente la predeterminada. Ninguna selección inicia
captura. La primera voz creada se convierte en predeterminada.

- **Agregar voz:** modal con nombre, micrófono, consentimiento, uso en RAM y límites experimentales.
- **Editar / reemplazar:** modal para capturar una nueva muestra y actualizar nombre/embedding del mismo
  identificador. Conserva el registro anterior hasta completar la extracción y la transacción. Cancelar o
  fallar no lo reemplaza. No es una edición de audio.
- **Usar por defecto:** confirma persistencia antes de actualizar la selección. Solo una voz predeterminada.
- **Eliminar:** modal con el nombre y confirmación «Eliminar permanentemente». No hay papelera ni deshacer
  dentro de la app. Si es predeterminada y quedan otras, primero debe elegirse otra predeterminada.
  Si es la única, puede eliminarse y queda la app sin perfil; reducción de ruido sigue disponible.

El borrado elimina el embedding activo y su metadata del catálogo de la app. No se promete borrado forense de
medios, WAL o copias externas. El historial de operaciones no es una colección de voces ni contiene embeddings.

## Backend y persistencia

El módulo `personal_voice` posee dominio, puerto `VoiceProfiles` y adaptador SQLCipher. Bootstrap inyecta el
puerto tanto al controlador de operaciones como al BFF. No se exponen embeddings en las consultas HTTP.

La migración es transaccional y preserva el embedding único anterior como «Voz anterior», predeterminada.
Copia el registro al catálogo y vacía la fila anterior dentro de la misma transacción; conserva la tabla antigua.
No sobrescribe registros si encuentra una combinación ambigua de tablas antiguas/nuevas: devuelve error y
preserva los datos. Abrir de nuevo no duplica la voz ni resucita un registro eliminado.

El catálogo usa identificadores UUID estables, nombre, embedding cifrado, indicador de predeterminada y fecha
UTC. Un índice único parcial impide dos predeterminadas. Nombres no vacíos, hasta 80 caracteres y sin caracteres
de control. SQL parametrizado y listados en una consulta; sin N+1. Límite configurado por Options con
`MIC_MAX_VOICE_PROFILES` (32 por defecto, rango 1–128).

No ejecutar binarios anteriores a esta migración sobre el catálogo nuevo: no conocen múltiples voces. Las API
antiguas siguen disponibles en el binario actualizado; la compatibilidad de downgrade no está implementada.

## Contratos

Todas las rutas requieren el token local y mantienen los controles de origen.

| Solicitud                                        | Resultado                                             |
| ------------------------------------------------ | ----------------------------------------------------- |
| `GET /v1/voice-profiles`                         | Metadata de voces; no embedding, audio ni clave       |
| `POST /v1/voice-profiles/{id}/default`           | `204` tras confirmar persistencia                     |
| `DELETE /v1/voice-profiles/{id}`                 | `204`; reintentar un borrado ya completado es inocuo  |
| `POST /v1/commands`, `enroll_voice_profile`      | `202` con operación; captura/extracción fuera de HTTP |
| `POST /v1/commands`, `start_voice_profile_audio` | `202` con operación; usa la voz indicada              |

El registro incluye `input_id`, `profile_id`, `name` y `replace`; mantiene `Idempotency-Key` y la correlación SSE.
La sesión personal incluye `input_id` y `voice_profile_id`. Los comandos anteriores `start_audio` y `enroll_voice`
se conservan para historiales/clientes anteriores: la sesión personal usa la predeterminada; el registro antiguo
solo reemplaza si hay una voz, y rechaza una selección ambigua si hay varias.

Predeterminada y eliminación son configuraciones inmediatas; no crean trabajos artificiales. Una transacción
inmediata consulta los trabajos de audio/registro y rechaza cambios con `409 audio_session_active`. El registro
asíncrono reutiliza la exclusión del journal. Los eventos de operación existentes comunican progreso/resultado;
los cambios confirmados del catálogo producen copias diagnósticas de eventos de negocio con identificador,
sin nombre, embedding ni audio. No se incorpora un bus ni un broker nuevo.

En React se inyecta `VoiceProfilesPort`, con Result y ACL que valida metadata y descarta campos privados.
El modal espera el estado terminal de la operación; no considera guardado el registro por recibir `202`.

## Verificación

Pruebas por módulo y runner central: migración/reapertura, SQL parametrizado, reemplazo, límite, predeterminada,
borrado idempotente, bloqueo durante captura, autorización HTTP y ausencia de embeddings en DTO. El ACL prueba
identificadores duplicados, fechas inválidas y predeterminadas ambiguas. La evidencia visual y de hardware se
actualiza en [T003](audio-validation.md). Calidad personal sigue dependiendo del benchmark T013.
