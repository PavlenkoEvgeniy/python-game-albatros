#!/usr/bin/env bash
# Build Debian and RPM installers from a PyInstaller one-file binary.
#
# Usage: build_packages.sh <version> <pyinstaller-binary> <output-dir>
# Set SKIP_RPM=1 to build only the .deb (useful on machines without rpmbuild).
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <version> <pyinstaller-binary> <output-dir>" >&2
  exit 2
fi

version=$1
binary=$2
outdir=$3
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

mkdir -p "$outdir"
architecture=$(dpkg --print-architecture)

# --- Debian package ---------------------------------------------------------
debroot="$workdir/deb"
install -Dm755 "$binary" "$debroot/usr/bin/albatross"
install -Dm644 "$repo_root/packaging/linux/albatross.desktop" \
  "$debroot/usr/share/applications/albatross.desktop"
install -Dm644 "$repo_root/packaging/linux/albatross.png" \
  "$debroot/usr/share/icons/hicolor/512x512/apps/albatross.png"

mkdir -p "$debroot/DEBIAN"
installed_size=$(du -sk "$debroot" | cut -f1)
cat > "$debroot/DEBIAN/control" <<EOF
Package: albatross
Version: $version
Section: games
Priority: optional
Architecture: $architecture
Maintainer: Pavlenko Evgeniy <pavlenkoevgeniy85@gmail.com>
Installed-Size: $installed_size
Depends: libc6
Description: A calm arcade game about an albatross gliding from a mountain
 Albatross is a small arcade game: the player launches from a mountain,
 glides over the valley and flaps to stay airborne. It is a self-contained
 PyInstaller build.
EOF
chmod 0644 "$debroot/DEBIAN/control"
dpkg-deb --build --root-owner-group "$debroot" \
  "$outdir/Albatross-$version-linux-$architecture.deb"

# --- RPM package ------------------------------------------------------------
if [ "${SKIP_RPM:-0}" = "1" ]; then
  echo "SKIP_RPM=1: rpm package not built" >&2
elif ! command -v rpmbuild >/dev/null 2>&1; then
  echo "rpmbuild is required to build the rpm package" >&2
  exit 1
else
  topdir="$workdir/rpm"
  mkdir -p "$topdir/BUILD" "$topdir/RPMS" "$topdir/SOURCES" \
    "$topdir/SPECS" "$topdir/SRPMS"
  cp "$binary" "$topdir/SOURCES/Albatross"
  cp "$repo_root/packaging/linux/albatross.desktop" "$topdir/SOURCES/"
  cp "$repo_root/packaging/linux/albatross.png" "$topdir/SOURCES/"
  sed "s/@VERSION@/$version/g" "$repo_root/packaging/linux/albatross.spec" \
    > "$topdir/SPECS/albatross.spec"
  rpmbuild --define "_topdir $topdir" -bb "$topdir/SPECS/albatross.spec"

  rpm_path=$(find "$topdir/RPMS" -name '*.rpm' -print -quit)
  cp "$rpm_path" "$outdir/Albatross-$version-linux-$(uname -m).rpm"
fi

echo "Packages written to $outdir:"
ls -1 "$outdir"
