#!/bin/bash
# ==============================================================================
# build_cdi.sh - Constructor de imágenes autoboot CDI para Dreamcast
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${1:-$REPO_ROOT/output_cdi}"
DUMMY_ARG="${2:-$DUMMY}"

python3 "$SCRIPT_DIR/build_cdi.py" "$OUTPUT_DIR" "$DUMMY_ARG"
