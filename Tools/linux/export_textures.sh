#!/bin/bash
# ==============================================================================
# export_textures.sh - Extrae masivamente todas las texturas de Marvel vs Capcom 2
# Utiliza el motor ModNao para generar imágenes PNG editables.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODNAO_DIR="$REPO_ROOT/Tools/modnao"
MVC2_DIR="${1:-$REPO_ROOT/MVC2}"
OUT_DIR="${2:-$REPO_ROOT/Extracted_Textures}"
FILTER="${3:-${ONLY:-${FILES:-$NAMES}}}"

echo "======================================================"
echo "    MVC2 Texture Extractor (ModNao Engine)"
echo "======================================================"
echo "  Origen : $MVC2_DIR"
echo "  Destino: $OUT_DIR"
if [ -n "$FILTER" ]; then
  echo "  Filtro : $FILTER"
fi
echo ""

cd "$MODNAO_DIR"
if [ -n "$FILTER" ]; then
  npx tsx src/cli/index.ts dump "$MVC2_DIR" "$OUT_DIR" "$FILTER"
else
  npx tsx src/cli/index.ts dump "$MVC2_DIR" "$OUT_DIR"
fi
