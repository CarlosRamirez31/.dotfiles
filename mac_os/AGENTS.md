# Reglas de desarrollo

- Usar exclusivamente pnpm, con la versión declarada en `packageManager` y un solo `pnpm-lock.yaml`. No usar npm, Yarn ni Bun para instalar o ejecutar scripts.
- Instalar con `pnpm install --frozen-lockfile`; regenerar el lockfile únicamente al modificar dependencias de forma deliberada.
- Mantener los controles de `pnpm-workspace.yaml`: antigüedad mínima de 24 horas, fuentes transitivas restringidas y scripts de dependencias revisados por versión exacta. No usar excepciones globales ni desactivar controles para superar errores.
- Guardar versiones directas exactas; revisar origen, licencia, scripts y cambios transitivos. Ejecutar `pnpm run security:audit` tras cambios de dependencias; no ejecutar correcciones forzadas sin evaluar su impacto.
- Verificar formato, lint, tipos y build pertinentes. No reformatear lockfiles ni artefactos generados.
- Seguir la arquitectura documentada en README: monolito modular, DDD, hexagonal, DI, Commons, eventos y sagas internos. No implementar funcionalidades fuera de lo solicitado.
