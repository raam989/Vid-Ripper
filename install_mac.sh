#!/bin/bash
# Vid-Ripper telepítő Macre.
# Megkeresi a Letöltések mappában a legfrissebb Vid-Rippert (a GitHub Releases oldaláról
# letöltött Mac zipet, a régi artifact zipet vagy a már kicsomagolt .app-ot), bemásolja az Alkalmazások
# mappába, és leszedi róla a karantén jelölést, így a Gatekeeper nem blokkolja.
#
# Futtatás a Terminalban (a fájlt be is húzhatod az ablakba a "bash " után):
#   bash ~/Downloads/install_mac.sh
# Másik mappából keresés:
#   bash install_mac.sh /útvonal/a/mappához

set -eo pipefail

APP_NAME="Vid-Ripper"
DEST="/Applications"
SRC_DIR="${1:-$HOME/Downloads}"

if [ ! -d "$SRC_DIR" ]; then
    echo "Nincs ilyen mappa: $SRC_DIR"
    exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Jelöltek: kicsomagolt .app, Mac zip, vagy a GitHub artifact zip (amiben a Mac zip van)
cands=()
while IFS= read -r -d '' f; do cands+=("$f"); done < <(
    find "$SRC_DIR" -maxdepth 3 \( \
        \( -type d -name "$APP_NAME.app" \) -o \
        \( -type f -name 'Vid-Ripper-*-Mac.zip' \) -o \
        \( -type f -name 'Vid-Ripper-macOS*.zip' \) \
    \) -not -path '*/__MACOSX/*' -print0 2>/dev/null)

if [ ${#cands[@]} -eq 0 ]; then
    echo "Nem találom a Vid-Rippert itt: $SRC_DIR"
    echo "Töltsd le a GitHub Releases oldaláról a Vid-Ripper-...-Mac.zip fájlt, és futtasd újra."
    exit 1
fi

# A legfrissebb (módosítási idő szerint)
SRC="$(ls -td -- "${cands[@]}" | head -1)"
echo "Forrás: $SRC"

case "$(basename "$SRC")" in
    *.app) APP_SRC="$SRC" ;;
    *-macOS*.zip)
        # artifact zip: kicsomagoljuk, benne a Mac zip
        ditto -x -k "$SRC" "$TMP/outer"
        inner="$(find "$TMP/outer" -name 'Vid-Ripper-*-Mac.zip' -type f | head -1)"
        if [ -z "$inner" ]; then echo "Az artifact zipben nincs Mac zip."; exit 1; fi
        ditto -x -k "$inner" "$TMP/app"
        APP_SRC="$TMP/app/$APP_NAME.app" ;;
    *.zip)
        ditto -x -k "$SRC" "$TMP/app"
        APP_SRC="$TMP/app/$APP_NAME.app" ;;
esac

if [ ! -d "$APP_SRC" ]; then
    echo "Nem sikerült kicsomagolni az appot."
    exit 1
fi

# Ha fut, bezárjuk
if pgrep -xq "$APP_NAME"; then
    echo "A Vid-Ripper fut, bezárom..."
    osascript -e "quit app \"$APP_NAME\"" >/dev/null 2>&1 || true
    sleep 2
fi

TARGET="$DEST/$APP_NAME.app"
SUDO=""
if [ ! -w "$DEST" ]; then
    echo "Az Alkalmazások mappába íráshoz kell a jelszavad."
    SUDO="sudo"
fi

if [ -d "$TARGET" ]; then
    echo "Régi verzió cseréje..."
    $SUDO rm -rf "$TARGET"
fi

$SUDO ditto "$APP_SRC" "$TARGET"
$SUDO xattr -cr "$TARGET"

echo "Kész: $TARGET"
open "$TARGET"
