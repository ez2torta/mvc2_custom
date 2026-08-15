#!/bin/bash
# ==============================================================================
# import_textures.sh - Reinyecta masivamente las texturas modificadas a MVC2
# Utiliza el motor ModNao para empaquetar PNGs a archivos .BIN de Dreamcast.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODNAO_DIR="$REPO_ROOT/Tools/modnao"
PNG_DIR="${1:-$REPO_ROOT/Extracted_Textures}"
MVC2_DIR="${2:-$REPO_ROOT/MVC2}"
OUT_MVC2_DIR="${3:-$REPO_ROOT/MVC2}"
FILTER="${4:-${ONLY:-${FILES:-$NAMES}}}"

echo "======================================================"
echo "    MVC2 Texture Injector (ModNao Engine)"
echo "======================================================"
echo "  Carpeta de PNGs: $PNG_DIR"
echo "  Plantilla Base : $MVC2_DIR"
echo "  Destino .BIN   : $OUT_MVC2_DIR"
if [ -n "$FILTER" ]; then
  echo "  Filtro         : $FILTER"
fi
echo ""

cd "$MODNAO_DIR"
if [ -n "$FILTER" ]; then
  npx tsx src/cli/index.ts inject "$PNG_DIR" "$MVC2_DIR" "$OUT_MVC2_DIR" "$FILTER"
else
  npx tsx src/cli/index.ts inject "$PNG_DIR" "$MVC2_DIR" "$OUT_MVC2_DIR"
fi
