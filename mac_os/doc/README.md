# Plan de la edición Local

Estado al 20 de octubre de 2026: implementación Local en desarrollo, con HTTP/SSE, persistencia y adaptadores de audio/IA. Las funcionalidades requieren verificaciones específicas; no es una beta completa. La beta se enfoca en macOS Apple Silicon; Intel se compila en CI, pero su soporte funcional requiere pruebas físicas.

| Documento                                       | Contenido                                                                    |
| ----------------------------------------------- | ---------------------------------------------------------------------------- |
| [Arquitectura](architecture.md)                 | Procesos, módulos, puertos, eventos, sagas y evolución Cloud.                |
| [Audio PCM](audio-transport.md)                 | Captura única, transporte, buffers, silencio y detección de voz.             |
| [Funcionalidades](features.md)                  | Alcance y criterios de aceptación por capacidad.                             |
| [IA local](local-ai.md)                         | Motores candidatos, licencias y ciclo de instalación.                        |
| [Instalación y desinstalación](installation.md) | Empaquetado de IA, instalador macOS, limpieza desde la app y Windows futuro. |
| [Persistencia](storage.md)                      | SQLite, cifrado, Keychain y perfiles.                                        |
| [Sprints y beta](sprints.md)                    | Secuencia, estimación y condiciones de salida.                               |
| [Pruebas](testing.md)                           | Automatización, audio real y métricas.                                       |
| [GitHub Actions](ci.md)                         | Workflow, artefactos y límites de validación.                                |

Decisiones del usuario: sin login; perfiles locales configurables; frontend y servicio local separados; el servicio solo vive mientras la aplicación está abierta; DDD, arquitectura hexagonal, DI, Commons, eventos internos y sagas; pnpm obligatorio. No hay broker externo. Cloud queda fuera de esta beta.

SQLCipher está integrado. Distribución, compatibilidad física y calendario de beta siguen sujetos a validación.

Contrato implementado: [HTTP/SSE y operaciones](control.md).

[Convenciones aprobadas de arquitectura](architecture-conventions.md): Options, Result, ACL, eventos, logs, SQL y pruebas por módulo.
