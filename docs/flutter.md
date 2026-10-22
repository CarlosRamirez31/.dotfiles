# Flutter opcional en Distrobox dev

Solo se instala al seleccionar `flutter` explícitamente, igual que Hermes:

```bash
./install.sh flutter
./install.sh workbench flutter  # si aún no están Podman y Distrobox
./install.sh all flutter        # instalación normal más Flutter
```

`./install.sh` y `./install.sh all` excluyen este componente. El instalador crea el perfil Arch `dev` si no existe y añade sus dependencias dentro del contenedor. No instala Java ni herramientas Android en el sistema principal.

Incluye Flutter estable (consultado al instalar), Dart incluido en Flutter, Java 21, Android CLI/SDK, ADB, build-tools, NDK y CMake acordes al SDK de Flutter. También descarga Android Emulator y la imagen Google APIs x86_64 del nivel de Android usado por Flutter, y crea el dispositivo virtual `Beambollow`. Las licencias se muestran para aceptación en la terminal.

Los SDKs van en `~/.local/share/flutter-dev/{flutter,android-sdk}` y las descargas en `~/.cache/flutter-dev/setup`. Son archivos del home compartido, pero su PATH solo se activa dentro de `dev`. `~/.config/flutter/env.zsh` se enlaza únicamente al instalar este componente. `ANDROID_AVD_HOME` apunta a `${XDG_CONFIG_HOME:-$HOME/.config}/.android/avd`, la carpeta usada para crear y descubrir los AVDs.

Se conservan los dispositivos virtuales existentes: nunca se usa `--force` ni se versionan sus imágenes, datos o claves de ADB. Se puede personalizar `FLUTTER_DEV_HOME`, `ANDROID_AVD_HOME` y `FLUTTER_AVD_NAME` antes de instalar; conserva esos valores en tu entorno si los cambias.

Al instalar este componente opcional se habilita el teclado físico del AVD (`hw.keyboard=yes`), tanto si se crea como si ya existe. Solo se ajusta esa propiedad; un emulador que ya esté abierto requiere reiniciarse para aplicarla. Puedes elegir el comportamiento al instalar:

```bash
FLUTTER_AVD_KEYBOARD=yes ./install.sh flutter   # habilitar (predeterminado)
FLUTTER_AVD_KEYBOARD=no ./install.sh flutter    # deshabilitar
FLUTTER_AVD_KEYBOARD=keep ./install.sh flutter  # conservar su configuración
```

```bash
distrobox enter dev
flutter doctor -v
flutter-emulator             # Beambollow, pantalla sin marco
flutter-emulator Otro_AVD    # otro dispositivo ya creado
cd ~/Projects/flutter_sanity_check
nvim lib/main.dart
```

En Neovim, `Space d e` selecciona y abre un emulador sin marco; `F5` selecciona un dispositivo arrancado e inicia la depuración. `F4` recarga, `Shift+F4` hace hot restart, `F9` alterna breakpoints y `Shift+F5` termina la sesión. Las configuraciones por proyecto se leen de `.vscode/launch.json`. El componente `nvim` proporciona esta integración y se instala por separado o con `all`.

En Awesome, la pantalla del emulador abre en mosaico como las demás aplicaciones. El área sobrante de su contenedor se recorta para mostrar el fondo, sin volver transparente la pantalla Android ni la barra de controles. El recorte sigue el tamaño que publica el emulador, incluida la rotación. Tú decides cuándo flota con `Alt+V`. Usa `Alt+clic derecho + arrastrar` o `Alt+Shift+clic derecho + arrastrar` para ajustar el tamaño libremente (activa el modo flotante), y `Alt+Shift+clic izquierdo + arrastrar` para moverlo.

La instalación inicial crea `~/Projects/flutter_sanity_check`, ejecuta análisis/pruebas y genera un APK. Si ese proyecto ya existe, lo conserva. No abre el emulador automáticamente. Para aceleración, el contenedor debe acceder al `/dev/kvm` del host; los permisos USB y KVM pertenecen al host.

Comprobaciones sin descargas:

```bash
./install.sh --dry-run all
./install.sh --dry-run flutter
python3 tests/flutter/test_optional.py
```
