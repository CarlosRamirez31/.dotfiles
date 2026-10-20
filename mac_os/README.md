# mac_os

Base de escritorio para macOS creada con Tauri 2, React y TypeScript. Este directorio es independiente de los componentes Linux del repositorio.

## Estado actual

Solo se inicializó el proyecto y su configuración de desarrollo. La ventana muestra una página mínima de bienvenida. Todavía no hay controles de audio, modelos de IA, micrófono virtual, icono en la barra de menús ni ejecución en segundo plano.

El objetivo posterior es una utilidad de barra de menús para controlar el micrófono y evaluar reducción de ruido y detección de voz personal. Estas funciones no están implementadas y los modelos no se descargan al instalar esta base.

## Tecnologías

- Tauri 2.12.4 y tauri-build 2.7.3; las dependencias nativas están fijadas en `src-tauri/Cargo.lock`.
- API JavaScript de Tauri: 2.12.4; CLI: 2.12.3. Los paquetes tienen versiones independientes.
- React 19, TypeScript 6 y Vite 8, con dependencias fijadas por `pnpm-lock.yaml`.
- Rust 1.92.0, edición 2024, fijado en `rust-toolchain.toml` con rustfmt y Clippy.

Se usa Tauri estable; la línea 3.x encontrada durante la inicialización está en fase alfa.

## Requisitos

- macOS y Xcode Command Line Tools (`xcode-select --install`).
- Node.js 22.22.3 y pnpm 11.1.1, utilizados en la validación inicial.
- Rustup: al ejecutar Cargo desde este directorio instala o selecciona el toolchain declarado.

Para esta base no hacen falta BlackHole, Python, PyTorch ni modelos de audio.

## Desarrollo

Desde la raíz del repositorio:

```bash
cd mac_os
pnpm install --frozen-lockfile
pnpm run tauri dev
```

`pnpm run dev` abre únicamente el servidor del frontend, sin el proceso nativo de Tauri.

## Validación

```bash
pnpm run format:check
pnpm run lint
pnpm run typecheck
pnpm run build
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo check --locked --manifest-path src-tauri/Cargo.toml
```

Para aplicar formato al frontend y la documentación: `pnpm run format`. Para Rust: `cargo fmt --manifest-path src-tauri/Cargo.toml`.

Los lockfiles se versionan. Las dependencias, `dist`, los esquemas generados y los artefactos de Cargo se excluyen de Git. Las comprobaciones de esta base no validan procesamiento de audio ni comportamiento de una futura utilidad de barra de menús.

## Compilación de escritorio

```bash
pnpm run tauri build
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

Las dependencias apuntan hacia dominio y aplicación. Los módulos se comunican mediante eventos internos con contratos públicos; no acceden a entidades privadas, adaptadores ni almacenamiento de otro módulo. Un núcleo compartido, si resulta necesario, será mínimo y no acumulará lógica de los módulos.

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

### Commons y configuración de módulos

La infraestructura compartida se organizará en una carpeta `commons`, con contratos propios e independientes.

Estructura objetivo, todavía no creada:

```text
src/
  commons/
    contracts/
    configuration/
    events/
    sagas/
  modules/<module>/
    domain/
    application/
    infrastructure/
    presentation/
    configuration/
  bootstrap/
src-tauri/src/
  commons/
    contracts/
    configuration/
    events/
    sagas/
  modules/<module>/
    domain/
    application/
    infrastructure/
    presentation/
    configuration/
  bootstrap/
```

`commons/configuration` contendrá los contratos de registro, metadatos, activación y validación de configuración de los módulos. Cada módulo conservará en su propia carpeta `configuration` sus opciones tipadas y el registro de sus casos de uso y adaptadores. `bootstrap` será la raíz de composición: leerá las opciones y conectará dependencias, módulos, suscriptores y sagas. No habrá lógica de negocio compartida ni referencias de Commons hacia implementaciones de módulos.

### Eventos internos y sagas

- El bus será propio, interno al proceso y en memoria, con publicadores y suscriptores inyectados. No se incorporarán Kafka, Redis, RabbitMQ ni adaptadores de mensajería externos en esta etapa.
- Cada evento público tendrá identificador, versión de contrato, módulo de origen y datos de correlación/causalidad. Sus datos serán serializables y no expondrán entidades privadas ni referencias a objetos del proceso.
- Los eventos de dominio permanecerán dentro del módulo. Los eventos entre módulos expresarán hechos de aplicación ya ocurridos; los handlers delegarán en casos de uso del módulo receptor.
- Frontend y backend tendrán su bus interno. El IPC de Tauri será un adaptador explícito para los contratos que deban cruzar esa frontera; no son un único bus en memoria ni se reenviarán eventos indiscriminadamente.
- Las sagas internas coordinarán procesos de varios módulos mediante eventos, con estado explícito, correlación, cancelación, tiempos límite y compensaciones. El módulo propietario definirá la saga; Commons aportará los contratos y mecanismos comunes.
- Una compensación será una operación de negocio explícita, no una transacción global ni una garantía de deshacer efectos irreversibles. Los handlers y compensaciones deberán tolerar duplicados cuando corresponda.
- La política de orden, errores y capacidad de colas se definirá en los contratos. Un bus en memoria no garantiza recuperar eventos tras cerrar o fallar el proceso; las sagas que necesiten recuperación tendrán un puerto de persistencia de estado y una política de reanudación.

El audio continuo no circulará como eventos de negocio por el bus general: utilizará puertos de streaming y canales acotados, con control de presión y cancelación. Los eventos comunicarán estado, configuración, resultados y fallos del procesamiento. Así se conserva la coordinación por eventos sin bloquear el hilo de audio.

### IA local o en servidores

Los casos de uso dependerán de puertos de procesamiento, nunca de un modelo local, Python, CoreAudio o un cliente de red concreto. Cada IA se integrará en su módulo mediante adaptadores intercambiables:

- Adaptador local: ejecuta el motor en el equipo.
- Adaptador remoto futuro: transmite audio y recibe resultados mediante un contrato de streaming versionado.

La configuración del módulo y la raíz de composición seleccionarán el adaptador; el dominio y los componentes React no conocerán el transporte. El acceso al hardware y la entrega al micrófono virtual seguirán en el equipo, aunque la inferencia se mueva a un servidor.

Esta separación facilita extraer módulos, pero no convierte automáticamente un bus local en un sistema distribuido. Antes de ejecutar IA remota habrá que implementar autenticación, consentimiento para transmitir audio, cifrado, límites de latencia, desconexión, cancelación y una política explícita de recuperación. No se cambiará silenciosamente entre procesamiento local y remoto. No se implementa ahora ningún transporte ni manejador externo de eventos.

## Gestor de paquetes y seguridad

Se usa exclusivamente pnpm 11.1.1, declarado en `packageManager`. No generar lockfiles de npm, Yarn ni Bun. Conservar `pnpm-lock.yaml` y usar `pnpm install --frozen-lockfile` para instalaciones reproducibles.

- Exigir al menos 24 horas desde la publicación de una versión (`minimumReleaseAge: 1440`). No desactivar esta protección para resolver una instalación.
- Bloquear fuentes exóticas en dependencias transitivas y fallar ante scripts de instalación no revisados. Solo permitir scripts por paquete y versión exacta, después de revisar su necesidad y contenido; no aprobar todos los scripts.
- Guardar dependencias directas con versión exacta. No actualizar ni aplicar correcciones forzadas automáticamente.
- Ejecutar `pnpm run security:audit` antes de entregar cambios de dependencias. Revisar vulnerabilidades y sus rutas; el audit no garantiza ausencia de paquetes maliciosos.
- No publicar tokens ni credenciales de registros. Revisar cambios del lockfile, origen y licencia de nuevas dependencias.
- Rust mantiene `Cargo.lock`; usar `cargo check --locked`. Los controles pnpm no cubren crates: revisar por separado cambios y avisos del ecosistema Rust.

Estas reglas están definidas en `pnpm-workspace.yaml` y `AGENTS.md`. No se han añadido automatizaciones de CI.
