#!/usr/bin/env bash
set -euo pipefail

# Same i3lock-color release as the desktop package; only the XKB label changes.
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
build=$(mktemp -d)
trap 'rm -rf -- "$build"' EXIT
curl --fail --location --silent --show-error \
    https://codeload.github.com/Raymo111/i3lock-color/tar.gz/refs/tags/2.13.c.5 \
    --output "$build/source.tar.gz"
printf '%s  %s\n' 46f15cbbf339873266e014f70b5e1ec02177f0295302b615a7bd85bef40d8ad2 "$build/source.tar.gz" | sha256sum --check
mkdir "$build/source"
tar -xzf "$build/source.tar.gz" -C "$build/source" --strip-components=1
cd "$build/source"
patch -p1 < "$root/i3lock-caps.patch"
autoreconf -fi
mkdir build
cd build
../configure --prefix=/usr --sysconfdir=/etc
make -j2
destination="$HOME/.local/opt/dotfiles-lock"
install -d "$destination"
install -m755 i3lock "$destination/i3lock.new"
mv -f "$destination/i3lock.new" "$destination/i3lock"
