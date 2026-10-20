# mac_os · Local

Prototipo macOS con Tauri, React y Rust. Un ejecutable funciona en dos modos: interfaz y servicio hijo.
El servicio arranca con la app y termina al salir. No hay login ni daemon permanente.

## Alcance implementado

- HTTP local para comandos y consultas; SSE para progreso, resultados y recuperación de eventos.
- Cola interna persistida en SQLCipher, sin broker, con idempotencia y cancelación.
- Captura CoreAudio mediante CPAL, PCM y buffers acotados; salida a **BlackHole 2ch**.
- RNNoise integrado mediante `nnnoiseless`, sin Python para el filtro de ruido.
- Adaptador experimental nomo-pvad + ERes2NetV2 para registro y filtrado por voz personal.
- Perfil de voz cifrado; la grabación de registro permanece en memoria y no se guarda como archivo.

La captura requiere inicio manual en esta versión. No están implementados la detección automática de
consumidores, barra de menús, múltiples perfiles configurables, instalador completo ni desinstalador.
No se ha acreditado compatibilidad de llamadas con Teams, Zoom, Meet o Slack. Voz personal **no separa
voces superpuestas** ni garantiza dejar pasar exclusivamente al propietario.

## Desarrollo

Requisitos: macOS, Xcode Command Line Tools, Node de `.nvmrc`, pnpm 11.1.1 y Rustup. Rust está fijado en
`rust-toolchain.toml`. Dependencias JavaScript y Rust exactas con lockfiles.

```bash
cd mac_os
pnpm install --frozen-lockfile
pnpm run tauri dev
```

Para voz personal, preparar una vez el runtime privado de desarrollo (macOS arm64 y Python 3.14):

```bash
python3 runtime/personal-voice/prepare.py
```

El script instala wheels por hash dentro de `.runtime/`, descarga artefactos oficiales verificados y no
abre el micrófono. No instala paquetes globales. Es tooling de desarrollo; el usuario final todavía no
dispone de un instalador que incluya Python y modelos. Véase [IA local](doc/local-ai.md).

Instalar [BlackHole 2ch](https://github.com/ExistentialAudio/BlackHole#installation-instructions)
por separado. Seleccionar micrófono físico en la app y BlackHole como entrada en la aplicación de llamadas.
Esta versión requiere dispositivos float32 de 48 kHz con uno o dos canales. No cambia el dispositivo
predeterminado del sistema. Registrar voz requiere detener una sesión previa; al comenzar el registro,
esperar la indicación de hablar durante diez segundos. El inicio permite gestionar voces con nombre y una predeterminada; editar reemplaza el registro solo tras completar la operación. Ver [gestión de voces](doc/voice-profiles.md).

## Arquitectura pequeña y modular

```text
React --HTTP--> BFF del servicio --comando persistido--> trabajador --> módulo
React <--SSE--- historial de eventos <---------------- resultado/progreso
CoreAudio --> PCM acotado --> RNNoise --> filtro personal opcional --> BlackHole
```

`modules/operations` contiene estado, casos de uso, puerto de persistencia y adaptadores SQLCipher/HTTP.
`modules/audio` contiene el flujo PCM y su adaptador CoreAudio. `ai_rnnoise` y `personal_voice` aíslan motores
concretos. `bootstrap` compone dependencias; `commons` contiene solamente contratos y configuración técnica.
El BFF no carga modelos. El frontend consume puertos inyectados y no importa SDK de IA.

Se crean capas cuando tienen responsabilidad real: no carpetas vacías, contenedor DI, bus genérico ni sagas
anticipadas. Las consultas simples permanecen síncronas. El inbox durable y las notificaciones Tokio son
suficientes para los comandos actuales. Una sesión de audio ocupa el trabajador hasta detenerla;
los diagnósticos aceptados mientras tanto esperan en cola. No se reanuda captura tras un reinicio.

Contratos, límites y pendientes: [arquitectura](doc/architecture.md), [control HTTP/SSE](doc/control.md),
[audio](doc/audio-transport.md) y [persistencia](doc/storage.md).

## Verificación

```bash
pnpm run format:check
pnpm run lint
pnpm run typecheck
pnpm test
pnpm run build
pnpm run security:audit
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo clippy --locked --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings
cargo test --locked --manifest-path src-tauri/Cargo.toml
pnpm run tauri build --bundles app -- --locked
```

El runtime de voz tiene pruebas con fixtures; instrucciones y evidencia en [pruebas](doc/testing.md).
Compilar no acredita captura, calidad de separación ni una llamada real. El bundle release incorpora RNNoise
y el adaptador Python; el runtime personal privado aún requiere preparación aparte.

## Paquetes y distribución

Usar exclusivamente pnpm para JavaScript, `--frozen-lockfile`, versiones exactas y las protecciones de
`pnpm-workspace.yaml`: 24 horas de antigüedad mínima, subdependencias restringidas y scripts revisados.
No añadir lockfiles de otros gestores ni desactivar controles. Cargo usa `Cargo.lock`; el runtime Python
usa wheels exactos y hashes en `runtime/personal-voice/requirements-arm64.lock`.

El workflow [macOS](../.github/workflows/macos.yml) valida y compila arm64/Intel, sin publicar una beta.
El runtime Python está fijado únicamente para arm64; Intel no dispone todavía de voz personal empaquetada.
Firma, notarización, licencias de distribución y desinstalación son puertas de beta, descritas en
[instalación](doc/installation.md), [sprints](doc/sprints.md) y [CI](doc/ci.md).

Cloud queda fuera de implementación. Su diseño mantiene HTTP/SSE de control y evalúa WebRTC + Opus para
audio remoto; gRPC se incorpora únicamente si un adaptador lo necesita.

Configuración por entorno: [Options y .env](doc/configuration.md). Pruebas por módulo: [runner central](test/README.md).
