# Perfiles locales de ajustes

Estado: requisito confirmado; diseño propuesto, CRUD pendiente (T007). Local no tiene cuentas ni login.
Una persona puede conservar varios perfiles, partir de plantillas predefinidas por la app y crear perfiles
personalizados. Un perfil de ajustes puede referenciar opcionalmente un perfil de voz; no son la misma entidad.

## Plantillas propuestas

Los nombres y valores iniciales siguientes son una propuesta de producto; no afirman calidad ya medida.
No agregan motores ni capacidades fuera del alcance de la beta.

| Plantilla       | Para quién / contexto                              | Reducción de ruido               | Voz personal                                    |
| --------------- | -------------------------------------------------- | -------------------------------- | ----------------------------------------------- |
| Reuniones       | Personas que usan Teams, Zoom, Meet o Slack        | Activada                         | Desactivada inicialmente                        |
| Entorno ruidoso | Trabajo compartido o remoto con ruido de fondo     | Activada                         | Opcional, tras registrar voz y explicar límites |
| Grabación       | Creadores que comparan señal original y procesada  | Activada; comparación voluntaria | Desactivada inicialmente                        |
| Personalizado   | Cualquier persona que necesita sus propios ajustes | Elección explícita               | Opcional                                        |

Reuniones y Entorno ruidoso pueden compartir valores iniciales: RNNoise todavía no ofrece aquí una intensidad
validada por contexto. No inventar niveles de potencia ni prometer separación de voces superpuestas.
Grabación es un conjunto de ajustes; no implica grabación permanente ni un editor de audio.

## Experiencia y aceptación

- Selector visible en el panel: nombre del perfil seleccionado y acceso a Administrar perfiles.
- Crear desde plantilla o desde Personalizado; pedir nombre y mostrar ajustes antes de guardar.
- Conservar plantillas de fábrica como punto de partida; Duplicar y personalizar crea una copia editable.
- Crear, renombrar, editar, duplicar y eliminar copias locales. Nunca borrar una plantilla de fábrica.
- Guardar confirma persistencia; error conserva el formulario y permite reintentar.
- Diferenciar perfil seleccionado de ajustes aplicados a una sesión. No indicar aplicación antes de confirmación.
- Elegir un perfil no concede permisos, descarga modelos, cambia la entrada predeterminada del sistema ni inicia captura.
- Si falta dispositivo, modelo o voz referenciada, indicar qué falta; no sustituir silenciosamente.
- Se admiten varias voces con nombre y una predeterminada, conforme a la ampliación confirmada del usuario.
  Los perfiles de ajustes podrán referenciarlas por identificador; ese CRUD de ajustes sigue pendiente.
  Ver [voces con nombre](voice-profiles.md).

## Persistencia y límites

Propuesta: módulo propietario de perfiles con puerto de repositorio, SQLCipher y consultas parametrizadas por
lotes; identificador estable de perfil, nombre, versión de esquema, origen de plantilla y ajustes soportados.
Las plantillas se versionan; una actualización no sobrescribe copias personalizadas. No guardar tokens,
embeddings ni audio dentro del objeto de ajustes: la voz es una referencia al módulo responsable.
HTTP sirve CRUD inmediato; solo procesamiento real usa operaciones 202. Emitir eventos de negocio después de
confirmar persistencia, sin convertir cada lectura en un trabajo ni enviar bloques PCM por el bus.

Antes de implementar T007 se debe acordar el cambio durante una sesión activa (aplicar en vivo o al reiniciar)
y la eliminación del perfil activo (bloquear o exigir seleccionar otro). Estas decisiones afectan al contrato;
esta especificación no modifica el comportamiento existente. Propuesta conservadora: aplicar cambios de
perfil en la próxima sesión y exigir otro perfil antes de eliminar el activo.

## Tareas y pruebas

T007 cubre plantillas, copias personalizadas y CRUD; T006 selector; T012 asociación a voz; T023 accesibilidad.
Probar varios perfiles de una misma persona, duplicación sin identidad compartida, reinicio, edición fallida,
referencia de voz eliminada, dispositivo ausente y evolución de plantillas sin perder personalizaciones.
No hay roles administrador/invitado ni sincronización Cloud en esta entrega.
