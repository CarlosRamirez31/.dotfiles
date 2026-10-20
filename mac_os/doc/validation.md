# Validación de la entrega de desarrollo

Fecha: 20 de octubre de 2026. Esta evidencia corresponde a la base Local en desarrollo, no a una beta
validada para llamadas. Las convenciones pendientes están en [architecture-conventions.md](architecture-conventions.md).

Comprobaciones locales realizadas:

- Prettier, ESLint y TypeScript: correctos.
- Build de React con Vite: correcto.
- Build Tauri de producción: bundle `mac_os.app` generado correctamente ; no acredita
  firma de distribución, notarización ni instalación de modelos.
- Node: cinco pruebas de SSE, Result, Options y ACL aprobadas.
- Rust: Clippy con warnings como errores, y dieciocho pruebas aprobadas de persistencia, recuperación,
  idempotencia, HTTP/SSE, cifrado, Options, limpieza, copias de eventos, logging y procesamiento.
- Prueba adicional del adaptador personal con runtime/modelo real: aprobada. No abre el micrófono;
  no mide la precisión de reconocimiento ni la compatibilidad con llamadas.
- Python: cuatro pruebas de la frontera del adaptador; Ruff lint y formato correctos.
- Auditoría pnpm: sin vulnerabilidades conocidas reportadas en esta ejecución.
- Workflow de GitHub Actions: validación estática con actionlint correcta; no equivale a ejecución remota.

La prueba SSE requiere abrir un puerto loopback. Falló inicialmente por la restricción del sandbox y
pasó al ejecutarse con ese permiso; no se omitió para aprobar la suite.

No se han validado sesiones reales con BlackHole, Teams, Zoom, Meet o Slack, ni un instalador completo,
notarización ni desinstalación. La limpieza por antigüedad, protección de archivos activos y Options
tienen pruebas automatizadas; no se ha observado una ejecución continua de 30 días.
Los modelos y el entorno Python de desarrollo no se incluyen en Git ni en el bundle actual.
