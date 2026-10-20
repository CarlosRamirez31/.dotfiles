# Entrada central de pruebas

Ejecutar desde `mac_os/`:

- `pnpm test`: frontend, Rust y contratos Python; falla ante cualquier suite requerida fallida.
- `pnpm run test:frontend`: Node, sin servicio ni modelos.
- `node test/run.mjs rust`: Cargo, incluye integración HTTP/SSE y SQLCipher.
- `node test/run.mjs python`: contratos Python sin importar SDK ni cargar pesos.
- `pnpm run test:models`: prueba real del adaptador personal con el runtime privado instalado; sin micrófono.

El runner busca suites Node en las carpetas de código; `test/rust.rs` registra las suites Rust de módulos
bajo `cfg(test)` y `test/python.py` registra el adaptador Python. No se importan tests en producción.
Los helpers entre módulos están en `test/support.rs`; los casos permanecen junto a su módulo.

Python utiliza por defecto `.runtime/personal-voice/venv/bin/python`. Para contratos sin modelos puede
seleccionarse Python 3.11 o posterior mediante `MIC_TEST_PYTHON=/ruta/python3`. Esa variable es exclusiva
del runner. Los tests reales de modelo mantienen el runtime CPython 3.14 fijado y sus dependencias.

La prueba SSE requiere permiso de abrir un puerto loopback. Las pruebas normales no capturan micrófono.
Una prueba de modelo omitida en la suite normal no se considera validación de IA ni de hardware.
