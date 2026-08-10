#!/usr/bin/env bash
# Fetch vendored fonts (both OFL-licensed) into assets/fonts/:
#   - SpaceGrotesk-VF.ttf      display font for English cover titles
#   - NotoSansCJKsc-Bold.otf   CJK fallback (Chinese category/fallback titles)
# Vendoring the font keeps the pipeline reproducible without system installs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$ROOT/assets/fonts"
mkdir -p "$DEST_DIR"

fetch() {
  local name="$1" url="$2"
  if [[ -f "$DEST_DIR/$name" ]]; then
    echo "Font already present: $DEST_DIR/$name"
    return
  fi
  echo "Downloading $name ..."
  curl -fL --progress-bar "$url" -o "$DEST_DIR/$name"
  echo "Saved: $DEST_DIR/$name"
}

fetch "SpaceGrotesk-VF.ttf" \
  "https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf"
fetch "NotoSansCJKsc-Bold.otf" \
  "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
