#!/usr/bin/env bash
set -euo pipefail
[[ ${CONTAINER_ID:-} == dev && -e /run/.containerenv ]] || {
    printf 'Este paso requiere Distrobox dev. Ejecuta ./install.sh rider desde el host.\n' >&2
    exit 1
}
[[ $EUID -ne 0 ]] || {
    printf 'Ejecuta el instalador como tu usuario normal, sin sudo.\n' >&2
    exit 1
}
command -v pacman >/dev/null || {
    printf 'Se requiere el perfil dev basado en Arch.\n' >&2
    exit 1
}
case $(uname -m) in
    x86_64) platform=linux ;;
    aarch64) platform=linuxARM64 ;;
    *)
        printf 'Arquitectura no compatible.\n' >&2
        exit 1
        ;;
esac

packages=(coreutils util-linux curl python tar gzip dotnet-sdk aspnet-runtime aspnet-targeting-pack gtk3 libxtst libxrender libxi libxrandr alsa-lib nss fontconfig freetype2 icu)
missing=()
for package in "${packages[@]}"; do
    pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
done
if ((${#missing[@]})); then
    sudo pacman -Syu --needed --noconfirm "${missing[@]}"
fi

rider_cache="${XDG_CACHE_HOME:-$HOME/.cache}/rider-dev/setup"
mkdir -p -- "$rider_cache"
curl --fail --silent --show-error --location --retry 3 \
    'https://data.services.jetbrains.com/products/releases?code=RD&latest=true&type=release' \
    --output "$rider_cache/releases.json.part"
mv -- "$rider_cache/releases.json.part" "$rider_cache/releases.json"
mapfile -t release < <(
    python3 - "$rider_cache/releases.json" "$platform" <<'PY'
import json, re, sys
release = json.load(open(sys.argv[1]))['RD'][0]
assert re.fullmatch(r'[0-9][A-Za-z0-9._-]*', release['version'])
download = release['downloads'][sys.argv[2]]
for key in ('link', 'checksumLink'):
    assert download[key].startswith('https://download.jetbrains.com/rider/')
print(release['version'])
print(download['link'])
print(download['checksumLink'])
PY
)
[[ ${#release[@]} == 3 ]] || {
    printf 'Manifiesto oficial inválido.\n' >&2
    exit 1
}
version=${release[0]}
archive="$rider_cache/${release[1]##*/}"
checksum="$archive.sha256"
curl --fail --silent --show-error --location --retry 3 "${release[2]}" --output "$checksum"
verify() {
    python3 - "$archive" "$checksum" <<'PY'
import hashlib, pathlib, re, sys
expected = pathlib.Path(sys.argv[2]).read_text().split()[0].lower()
assert re.fullmatch(r'[a-f0-9]{64}', expected), 'Checksum oficial inválido'
with open(sys.argv[1], 'rb') as stream:
    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
if actual != expected:
    raise SystemExit('Checksum de Rider incorrecto')
PY
}

install_root=/opt/rider
destination="$install_root/$version"
if [[ ! -x $destination/bin/rider ]]; then
    [[ ! -e $destination ]] || {
        printf 'Destino existente incompleto: %s\n' "$destination" >&2
        exit 1
    }
    if [[ ! -f $archive ]] || ! verify; then
        printf 'Descargando Rider %s desde JetBrains...\n' "$version"
        curl --fail --silent --show-error --location --retry 3 --continue-at - \
            "${release[1]}" --output "$archive.part"
        mv -- "$archive.part" "$archive"
    fi
    verify
    sudo install -d -m 0755 "$install_root"
    stage=$(sudo mktemp -d "$install_root/.install.XXXXXX")
    trap 'sudo rm -rf -- "$stage"' EXIT
    sudo tar --extract --gzip --file "$archive" --directory "$stage" --strip-components=1 --no-same-owner
    sudo test -x "$stage/bin/rider" || {
        printf 'El archivo no contiene el lanzador de Rider.\n' >&2
        exit 1
    }
    sudo chmod 0755 "$stage"
    sudo mv -- "$stage" "$destination"
    trap - EXIT
fi
if [[ -e $install_root/current && ! -L $install_root/current ]]; then
    printf '%s/current existe y no es un enlace; no se modificó.\n' "$install_root" >&2
    exit 1
fi
sudo ln -sfn -- "$destination" "$install_root/current"
component_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
sudo ln -sfn -- "$component_root/dotfiles/.local/bin/rider" /usr/local/bin/rider
printf 'Rider %s instalado en %s\n' "$version" "$destination"
dotnet --list-sdks
