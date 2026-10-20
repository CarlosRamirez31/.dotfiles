# mac_os

Base de escritorio para macOS creada con Tauri 2, React y TypeScript. Este directorio es independiente de los componentes Linux del repositorio.

## Estado actual

Solo se inicializó el proyecto y su configuración de desarrollo. La ventana muestra una página mínima de bienvenida. Todavía no hay controles de audio, modelos de IA, micrófono virtual, icono en la barra de menús ni ejecución en segundo plano.

El objetivo posterior es una utilidad de barra de menús para controlar el micrófono y evaluar reducción de ruido y detección de voz personal. Estas funciones no están implementadas y los modelos no se descargan al instalar esta base.

## Tecnologías

- Tauri 2.12.4 y tauri-build 2.7.3; las dependencias nativas están fijadas en `src-tauri/Cargo.lock`.
- API JavaScript de Tauri: 2.12.4; CLI: 2.12.3. Los paquetes tienen versiones independientes.
- React 19, TypeScript 6 y Vite 8, con dependencias fijadas por `package-lock.json`.
- Rust 1.92.0, edición 2024, fijado en `rust-toolchain.toml` con rustfmt y Clippy.

Se usa Tauri estable; la línea 3.x encontrada durante la inicialización está en fase alfa.

## Requisitos

- macOS y Xcode Command Line Tools (`xcode-select --install`).
- Node.js 22.22.3 y npm 10.9.8, utilizados en la validación inicial.
- Rustup: al ejecutar Cargo desde este directorio instala o selecciona el toolchain declarado.

Para esta base no hacen falta BlackHole, Python, PyTorch ni modelos de audio.

## Desarrollo

Desde la raíz del repositorio:

```bash
cd mac_os
npm ci
npm run tauri dev
```

`npm run dev` abre únicamente el servidor del frontend, sin el proceso nativo de Tauri.

## Validación

```bash
npm run format:check
npm run lint
npm run typecheck
npm run build
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo check --locked --manifest-path src-tauri/Cargo.toml
```

Para aplicar formato al frontend y la documentación: `npm run format`. Para Rust: `cargo fmt --manifest-path src-tauri/Cargo.toml`.

Los lockfiles se versionan. Las dependencias, `dist`, los esquemas generados y los artefactos de Cargo se excluyen de Git. Las comprobaciones de esta base no validan procesamiento de audio ni comportamiento de una futura utilidad de barra de menús.

## Compilación de escritorio

```bash
npm run tauri build
```

Los artefactos se generan en `src-tauri/target/release/bundle`. La firma y notarización para distribución se configurarán cuando se defina la publicación de la aplicación.

## Estructura

- `src/`: frontend React.
- `src-tauri/src/`: entrada nativa en Rust.
- `src-tauri/tauri.conf.json`: configuración de Tauri.
- `src-tauri/capabilities/`: permisos del frontend.

## Referencias

- [Crear un proyecto Tauri](https://v2.tauri.app/start/create-project/).
- [Requisitos para macOS](https://v2.tauri.app/start/prerequisites/).
- [Icono en la barra de menús](https://v2.tauri.app/learn/system-tray/).

## Arquitectura acordada

La aplicación será un **monolito modular**: un único producto de escritorio, con módulos internos delimitados por capacidad. Cada IA y cada capacidad necesaria tendrá su propio módulo. Tanto frontend como backend nativo aplicarán **DDD, arquitectura hexagonal e inyección de dependencias**.

### Capas de cada módulo

- `domain`: entidades, objetos de valor, invariantes y servicios de dominio. Sin dependencias de React, Tauri, CoreAudio, almacenamiento o motores de IA.
- `application`: casos de uso y puertos de entrada/salida mediante interfaces o traits; depende del dominio.
- `infrastructure`: adaptadores de modelos, dispositivos, persistencia y servicios del sistema; implementa los puertos.
- `presentation`: componentes y controladores React en frontend; comandos y eventos Tauri como adaptadores de entrada en Rust.

Las dependencias apuntan hacia dominio y aplicación. Los módulos se comunican mediante contratos públicos de aplicación o eventos explícitos; no acceden a entidades privadas, adaptadores ni almacenamiento de otro módulo. Un núcleo compartido, si resulta necesario, será mínimo y no acumulará lógica de los módulos.

### Inyección de dependencias

- **Frontend:** interfaces TypeScript para los puertos, dependencias por constructor o factoría y composición central al iniciar React. Context puede distribuir instancias ya compuestas; los componentes no crean adaptadores Tauri ni invocan IPC directamente.
- **Backend Rust:** traits como puertos, dependencias por constructor y composición central al iniciar Tauri. `Arc` y el estado administrado de Tauri se usarán cuando corresponda. Los comandos delegarán en casos de uso, sin lógica de negocio.
- Los DTO del IPC serán contratos de frontera, separados de las entidades de dominio. Ningún módulo dependerá de un contenedor global para localizar servicios.

### Módulos previstos

| Módulo              | Responsabilidad                                                    |
| ------------------- | ------------------------------------------------------------------ |
| `microphone`        | Selección de entrada, estado y control del micrófono.              |
| `noise-suppression` | Reducción de ruido y contrato de procesamiento.                    |
| `personal-voice`    | Registro del perfil personal y detección de voz.                   |
| `audio-pipeline`    | Coordinación del flujo de audio mediante puertos de procesamiento. |
| `virtual-audio`     | Entrega del audio procesado a una entrada virtual de macOS.        |
| `preferences`       | Preferencias locales de la aplicación.                             |
| `desktop-shell`     | Barra de menús, panel, atajos y ciclo de vida.                     |

Cada motor de IA incorporado tendrá su módulo de integración separado, implementando los puertos de la capacidad correspondiente. RNNoise, DeepFilterNet y nomo-pvad son candidatos: todavía no se han seleccionado ni instalado para macOS. Las capacidades se reflejarán en frontend y backend según sus necesidades, sin crear interfaces visuales para módulos exclusivamente internos.

Esta sección fija la dirección arquitectónica. El scaffold actual todavía no implementa los módulos, sus contratos ni la composición de dependencias.
