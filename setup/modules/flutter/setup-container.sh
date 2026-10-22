#!/usr/bin/env bash
# Install only inside the existing dev container; never install packages on the host.
set -euo pipefail

[[ ${CONTAINER_ID:-} == dev && -e /run/.containerenv ]] || {
    printf 'Ejecuta ./install.sh flutter desde el host; este paso requiere el contenedor dev.\n' >&2
    exit 1
}
export ANDROID_AVD_HOME="${ANDROID_AVD_HOME:-${XDG_CONFIG_HOME:-$HOME/.config}/.android/avd}"
case ${FLUTTER_AVD_KEYBOARD:-yes} in
    yes | no | keep) ;;
    *)
        printf 'FLUTTER_AVD_KEYBOARD debe ser yes, no o keep.\n' >&2
        exit 1
        ;;
esac

[[ $EUID -ne 0 ]] || {
    printf 'Ejecuta esto como tu usuario normal, sin sudo.\n' >&2
    exit 1
}
command -v pacman >/dev/null || {
    printf 'Este instalador requiere Arch Linux.\n' >&2
    exit 1
}
install_packages() {
    local package
    local -a missing=()
    for package in "$@"; do
        pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
    done
    if ((${#missing[@]})); then
        sudo pacman -Syu --needed "${missing[@]}"
    fi
}
[[ $(uname -m) == x86_64 ]] || {
    printf 'Este instalador requiere Arch x86_64.\n' >&2
    exit 1
}

dev_tools="${FLUTTER_DEV_HOME:-$HOME/.local/share/flutter-dev}"
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/flutter-dev/setup"
sdk_flutter="$dev_tools/flutter"
export ANDROID_HOME="$dev_tools/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
mkdir -p -- "$cache_root"

fetch() {
    local url=$1 destination=$2
    curl --fail --location --retry 2 --connect-timeout 15 --output "$destination.part" "$url" || return
    mv -- "$destination.part" "$destination"
}

printf 'Consultando la versión estable oficial de Flutter...\n'
if ! fetch https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json "$cache_root/flutter.json"; then
    printf 'No se pudo descargar Flutter. Ejecuta este script desde una terminal con acceso a Internet.\n' >&2
    exit 1
fi
fetch https://dl.google.com/android/repository/repository2-3.xml "$cache_root/android.xml"

install_packages curl git unzip xz python jdk21-openjdk clang cmake ninja gtk3 pkgconf libpulse nss libxkbcommon-x11 mesa vulkan-icd-loader
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-21-openjdk}"
export PATH="$sdk_flutter/bin:$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"

# Resolve the current release each time instead of pinning a Flutter version.
mapfile -t flutter_release < <(
    python3 - "$cache_root/flutter.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
release = next(r for r in data['releases'] if r['hash'] == data['current_release']['stable'] and r.get('dart_sdk_arch', 'x64') == 'x64')
print(data['base_url'] + '/' + release['archive'])
print(release['sha256'])
print(release['version'])
PY
)
[[ ${#flutter_release[@]} == 3 ]] || {
    printf 'Manifiesto de Flutter inválido.\n' >&2
    exit 1
}

verify() {
    python3 - "$1" "$2" <<'PY'
import hashlib, sys
expected = sys.argv[2].strip().lower()
algorithm = {40: 'sha1', 64: 'sha256'}[len(expected)]
with open(sys.argv[1], 'rb') as stream:
    actual = hashlib.file_digest(stream, algorithm).hexdigest()
if actual != expected:
    raise SystemExit('Checksum incorrecto: ' + sys.argv[1])
PY
}

if [[ ! -x $sdk_flutter/bin/flutter ]]; then
    [[ ! -e $sdk_flutter ]] || {
        printf 'La ruta ya existe y no es un SDK: %s\n' "$sdk_flutter" >&2
        exit 1
    }
    bundle="$cache_root/flutter-${flutter_release[2]}.tar.xz"
    if [[ ! -f $bundle ]] || ! verify "$bundle" "${flutter_release[1]}"; then
        fetch "${flutter_release[0]}" "$bundle"
    fi
    verify "$bundle" "${flutter_release[1]}"
    mkdir -p -- "$(dirname -- "$sdk_flutter")"
    stage=$(mktemp -d "$(dirname -- "$sdk_flutter")/.flutter-install.XXXXXX")
    trap 'rm -rf -- "$stage"' EXIT
    tar -xf "$bundle" -C "$stage"
    mv -- "$stage/flutter" "$sdk_flutter"
    rm -rf -- "$stage"
    trap - EXIT
else
    [[ $(git -C "$sdk_flutter" branch --show-current) == stable ]] || {
        printf 'El SDK existente no está en stable; no se cambiará su canal: %s\n' "$sdk_flutter" >&2
        exit 1
    }
    "$sdk_flutter/bin/flutter" upgrade
fi

# Bootstrap the newest stable Linux command-line tools from Google's repository.
if [[ ! -x $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager ]]; then
    mapfile -t android_tools < <(
        python3 - "$cache_root/android.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
packages = []
for package in root.findall('remotePackage'):
    if not package.get('path', '').startswith('cmdline-tools;'):
        continue
    channel = package.find('channelRef')
    if package.find('obsolete') is not None or (channel is not None and channel.get('ref') != 'channel-0'):
        continue
    revision = package.find('revision')
    if revision.find('preview') is not None:
        continue
    version = tuple(int(revision.findtext(key, '0')) for key in ('major', 'minor', 'micro'))
    for archive in package.findall('./archives/archive'):
        if archive.findtext('host-os') == 'linux':
            complete = archive.find('complete')
            packages.append((version, complete.findtext('url'), complete.findtext('checksum')))
if not packages:
    raise SystemExit('No se encontraron herramientas estables de Android para Linux.')
_, url, checksum = max(packages)
print('https://dl.google.com/android/repository/' + url)
print(checksum)
PY
    )
    [[ ${#android_tools[@]} == 2 ]] || {
        printf 'Manifiesto de Android inválido.\n' >&2
        exit 1
    }
    fetch "${android_tools[0]}" "$cache_root/android-tools.zip"
    verify "$cache_root/android-tools.zip" "${android_tools[1]}"
    stage=$(mktemp -d "$cache_root/android-install.XXXXXX")
    trap 'rm -rf -- "$stage"' EXIT
    unzip -q "$cache_root/android-tools.zip" -d "$stage"
    mkdir -p -- "$ANDROID_HOME/cmdline-tools"
    [[ ! -e $ANDROID_HOME/cmdline-tools/latest ]] || {
        printf 'Ya existe cmdline-tools/latest pero no contiene sdkmanager; revísalo antes de continuar.\n' >&2
        exit 1
    }
    mv -- "$stage/cmdline-tools" "$ANDROID_HOME/cmdline-tools/latest"
    rm -rf -- "$stage"
    trap - EXIT
fi

# Read Android versions from the installed Flutter SDK, including its exact NDK.
mapfile -t android_versions < <(
    python3 - "$sdk_flutter" "$cache_root/android.xml" <<'PY'
import pathlib, re, sys, xml.etree.ElementTree as ET
extension = pathlib.Path(sys.argv[1], 'packages/flutter_tools/gradle/src/main/kotlin/FlutterExtension.kt').read_text()
api = re.search(r'compileSdkVersion\s*:\s*Int\s*=\s*(\d+)', extension).group(1)
ndk = re.search(r'ndkVersion\s*:\s*String\s*=\s*"([^"]+)"', extension).group(1)
versions = []
for package in ET.parse(sys.argv[2]).getroot().findall('remotePackage'):
    match = re.fullmatch(r'build-tools;(\d+)\.(\d+)\.(\d+)', package.get('path', ''))
    if match and match[1] == api:
        versions.append(tuple(map(int, match.groups())))
if not versions:
    raise SystemExit('No hay build-tools estables para Android API ' + api)
print(api)
print(ndk)
print('.'.join(map(str, max(versions))))
PY
)
[[ ${#android_versions[@]} == 3 ]] || {
    printf 'No se pudieron determinar las versiones de Android.\n' >&2
    exit 1
}
sdkmanager="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
printf '\nLee y acepta las licencias de Android para continuar:\n'
"$sdkmanager" --sdk_root="$ANDROID_HOME" --licenses
"$sdkmanager" --sdk_root="$ANDROID_HOME" --install \
    'platform-tools' 'cmdline-tools;latest' 'emulator' \
    "platforms;android-${android_versions[0]}" "build-tools;${android_versions[2]}" \
    "ndk;${android_versions[1]}" 'cmake;3.22.1' \
    "system-images;android-${android_versions[0]};google_apis;x86_64"

# Preserve existing AVDs and userdata. Match the emulator's discovery directory.
mkdir -p -- "$ANDROID_AVD_HOME"
avd_name="${FLUTTER_AVD_NAME:-Beambollow}"
[[ $avd_name =~ ^[a-zA-Z0-9._-]+$ ]] || {
    printf 'Nombre de AVD inválido.\n' >&2
    exit 1
}
if [[ ! -e $ANDROID_AVD_HOME/$avd_name.ini ]]; then
    "$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager" create avd \
        --name "$avd_name" \
        --package "system-images;android-${android_versions[0]};google_apis;x86_64" \
        --device pixel <<<no
fi
python3 "$(dirname -- "${BASH_SOURCE[0]}")/configure-avd.py" \
    "$ANDROID_AVD_HOME/$avd_name.avd/config.ini" "${FLUTTER_AVD_KEYBOARD:-yes}"
"$ANDROID_HOME/emulator/emulator" -list-avds

flutter config --android-sdk "$ANDROID_HOME"
flutter config --jdk-dir "$JAVA_HOME"
flutter precache --android

# USB permissions are managed by the host; do not change its udev rules here.
flutter doctor -v
adb devices -l
flutter devices

printf '\nVerificando un proyecto Android de prueba...\n'
smoke_project="$HOME/Projects/flutter_sanity_check"
if [[ ! -e $smoke_project ]]; then
    mkdir -p -- "$HOME/Projects"
    flutter create --platforms=android --project-name flutter_sanity_check "$smoke_project"
    (
        cd -- "$smoke_project"
        flutter analyze
        flutter test
        flutter build apk --debug
    )
else
    printf 'El proyecto ya existe; se conserva sin modificar: %s\n' "$smoke_project"
fi
printf '\nInstalación terminada dentro de dev. Vuelve a entrar en dev para cargar el PATH. Conecta el Android y acepta su autorización RSA.\n'
printf 'Dentro de dev, abre nvim en tu proyecto, entra en lib/main.dart y pulsa F5.\n'
printf 'Emulador sin marco: flutter-emulator | En Neovim: Space d e\n'
