# GitHub Actions

Workflow: `.github/workflows/macos.yml`, ubicado en la raíz del repositorio porque GitHub no descubre workflows bajo `mac_os/`.

Se ejecuta en pushes a `mac_os`, PR que modifiquen la app/workflow y mediante ejecución manual. Dos jobs de la matriz: `macos-15` arm64 y `macos-15-intel` x64, cada uno con build nativo. No se fuerza cross-compilation ni se promete compatibilidad de hardware por pasar el build.

Pasos: checkout, Node fijado por `.nvmrc`, pnpm fijado por `packageManager`, Rust/rustfmt/Clippy fijados por `rust-toolchain.toml`, instalación congelada, formato, lint, tipos, audit, Clippy, tests Rust y build Tauri release `.app`.

El build usa el lockfile de Cargo. Se comprime el bundle `.app` en tar.gz para conservar su estructura/permisos y se adjunta al run durante 14 días. No se crea Release, tag, DMG público ni actualización automática. Las Actions se fijan por SHA, el token solo lee contenido y no se usan secretos ni `pull_request_target`.

Son artefactos de comprobación sin identidad Developer ID ni notarización. No equivalen a beta externa distribuible. Para esa fase: certificado y credenciales Apple mediante secrets, firma del host y del sidecar, entitlements mínimos, notarización y verificación en otro equipo. No deshabilitar Gatekeeper como procedimiento del producto.

La auditoría requiere acceso al registro: un error de red debe fallar, no convertirse en «sin vulnerabilidades». Los controles pnpm no auditan crates. Añadir análisis de avisos Rust antes de beta con una herramienta fijada y revisada; no se afirma cobertura de vulnerabilidades Rust hoy.

Validación local del YAML/formato y build no equivale a un run remoto verde. El primer run debe revisarse después de un push autorizado. Al crear el sidecar habrá que actualizar empaquetado y matriz; hoy no hay servicio ni modelos para empaquetar.

Fuentes: [Tauri en GitHub Actions](https://v2.tauri.app/distribute/pipelines/github/), [firma macOS](https://v2.tauri.app/distribute/sign/macos/), [runners GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [artefactos](https://github.com/actions/upload-artifact).

## Evidencia local del 20 de octubre de 2026

Pasaron Prettier, ESLint, TypeScript, build Vite, Clippy con warnings como error y validación del workflow con actionlint 1.7.12. `cargo test --locked` terminó correctamente con **0 tests**: todavía no hay cobertura funcional.

El comando del workflow `pnpm run tauri build --bundles app -- --locked` generó localmente el bundle arm64 `src-tauri/target/release/bundle/macos/mac_os.app` (3,97 MiB). Es solo el scaffold, sin servicio ni modelos. No se ha abierto/probado una sesión de audio ni se ha ejecutado el workflow en GitHub. El build Intel, firma Developer ID y notarización siguen sin verificar.

## Evolución a instalador completo

El workflow actual sigue compilando solo el scaffold `.app`. La etapa futura de release preparará sidecar, runtimes, modelos verificados, inventario y licencias antes de `tauri build`; después construirá PKG firmado/notarizado y verificará instalación/desinstalación en entorno dedicado. No ejecutar el instalador en el runner de compilación ni incorporar pesos sin licencia. Detalles en [installation.md](installation.md). No hay PKG ni desinstalador implementados todavía.
