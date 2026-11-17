#!/usr/bin/env bash
# Wrap a PyInstaller .app bundle into a distributable disk image.
#
# Usage: build_dmg.sh <version> <app-bundle> <output-dir>
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <version> <app-bundle> <output-dir>" >&2
  exit 2
fi

version=$1
app_bundle=$2
outdir=$3

if [ ! -d "$app_bundle" ]; then
  echo "app bundle not found: $app_bundle" >&2
  exit 1
fi

mkdir -p "$outdir"
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

cp -R "$app_bundle" "$workdir/"
ln -s /Applications "$workdir/Applications"

hdiutil create -volname "Albatross" \
  -srcfolder "$workdir" -ov -format UDZO \
  "$outdir/Albatross-$version-macos.dmg"

echo "Disk image written to $outdir/Albatross-$version-macos.dmg"
