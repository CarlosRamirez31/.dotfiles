# Reglas de desarrollo

- Usar exclusivamente pnpm, con la versión declarada en `packageManager` y un solo `pnpm-lock.yaml`. No usar npm, Yarn ni Bun para instalar o ejecutar scripts.
- Instalar con `pnpm install --frozen-lockfile`; regenerar el lockfile únicamente al modificar dependencias de forma deliberada.
- Mantener los controles de `pnpm-workspace.yaml`: antigüedad mínima de 24 horas, fuentes transitivas restringidas y scripts de dependencias revisados por versión exacta. No usar excepciones globales ni desactivar controles para superar errores.
- Guardar versiones directas exactas; revisar origen, licencia, scripts y cambios transitivos. Ejecutar `pnpm run security:audit` tras cambios de dependencias; no ejecutar correcciones forzadas sin evaluar su impacto.
- Verificar formato, lint, tipos y build pertinentes. No reformatear lockfiles ni artefactos generados.
- Seguir la arquitectura documentada en README: monolito modular, DDD, hexagonal, DI, Commons, eventos y sagas internos. No implementar funcionalidades fuera de lo solicitado.
- Aplicar `doc/architecture-conventions.md`: Options tipadas e inyectadas, Result y ACL en adaptadores de IA, eventos de negocio sin bloques de audio ni logs técnicos en el bus.
- Parametrizar valores SQL y evitar N+1 mediante consultas por lotes; preservar transacciones y contratos.
- Cada módulo será dueño de su carpeta `test/`; `test/` del proyecto coordina su ejecución. No presentar estructura documentada como runner implementado.
- Logs y copias diagnósticas locales: retención por antigüedad de 30 días; SQLCipher conserva la recuperación. No guardar audio, embeddings ni secretos en logs.

<!-- global-typed-flow-and-views:start -->

# Estados tipados y separación de vistas (2026-10-20)

Reglas generales aprobadas por el usuario para todos los proyectos de Codex, tanto frontend como backend.

- No comparar estados, acciones, tipos de operación, modos ni códigos de negocio contra texto literal suelto.
  Usar enums para conjuntos cerrados; constantes tipadas cuando el lenguaje, el contrato o el runtime no
  permitan un enum adecuado. Conservar los valores serializados de los contratos existentes.
- Convertir respuestas externas y formatos de proveedor a tipos internos en ACL/adaptadores. Centralizar las
  constantes de protocolos/configuración; no propagar texto de proveedores como decisiones de negocio.
- En React, separar estado, efectos, coordinación y handlers en hooks; extraer reglas, selectores y mensajes a
  funciones o módulos propios. Las vistas se centran en HTML/JSX y enlaces a los handlers del hook, sin
  peticiones, persistencia, transiciones de negocio ni bloques de lógica dentro del JSX.
- Evitar ternarios anidados para decidir estados o mensajes. Usar funciones de presentación y mapas tipados.
- Aplicar las reglas al código nuevo o modificado y revisar los flujos relacionados. No cambiar contratos,
  datos ni comportamiento existente por una refactorización. Las validaciones intrínsecas del lenguaje y las
  fixtures de contrato no sustituyen decisiones de negocio tipadas.

- No encadenar operadores ternarios ni concentrar lógica extensa en expresiones difíciles de leer. Usar mapas
  tipados para traducciones, `if`/`switch` para decisiones y Strategy cuando existan comportamientos de negocio
  intercambiables que lo justifiquen. No introducir Strategy para sustituir un mapa simple o por el número de ramas.

<!-- global-typed-flow-and-views:end -->

## Controladores y servicios por responsabilidad

- Separar controladores por recurso o flujo; no concentrar endpoints y responsabilidades en un archivo.
- Los controladores reciben y validan el formato HTTP, llaman servicios de aplicación y traducen respuestas. Las reglas de negocio y la coordinación de persistencia pertenecen a aplicación/dominio.
- Mantener rutas, seguridad, conversión de errores y transporte SSE en archivos propios. Los servicios de aplicación no dependen de Axum.
- Usar `commons/utils/` solo para utilidades técnicas compartidas. Las utilidades específicas permanecen en su módulo; no trasladar reglas de negocio a utilidades genéricas.
