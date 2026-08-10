#!/bin/bash
# ==============================================================================
# build_cdi.sh - Constructor de imágenes autoboot CDI (MIL-CD) para Dreamcast
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MVC2_DATA="$REPO_ROOT/MVC2"
OUTPUT_DIR="${1:-$REPO_ROOT/output_cdi}"
OUTPUT_CDI="$OUTPUT_DIR/mvc2_custom.cdi"
TEMP_BUILD="/tmp/dc_cdi_build_$$"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$TEMP_BUILD/data"

echo "======================================================"
echo "    Dreamcast CDI Builder para Marvel vs Capcom 2"
echo "======================================================"

# 1. Comprobar herramientas
ISO_TOOL=""
if command -v genisoimage &> /dev/null; then
    ISO_TOOL="genisoimage"
elif command -v mkisofs &> /dev/null; then
    ISO_TOOL="mkisofs"
else
    echo "[!] Error: Se requiere 'genisoimage' o 'mkisofs'."
    echo "    Instálalo con: sudo apt install genisoimage"
    exit 1
fi

echo "[*] 1/4 Copiando archivos de juego a directorio temporal..."
cp -r "$MVC2_DATA"/* "$TEMP_BUILD/data/"

echo "[*] 2/4 Asegurando que 1ST_READ.BIN esté SCRAMBLED..."
"$SCRIPT_DIR/scramble" "$MVC2_DATA/1ST_READ.BIN" "$TEMP_BUILD/data/1ST_READ.BIN"

echo "[*] 3/4 Generando IP.BIN con metadatos de MvC2..."
python3 "$SCRIPT_DIR/make_ipbin.py"

echo "[*] 4/4 Creando imagen ISO a LBA 11702..."
$ISO_TOOL -C 0,11702 -V "MARVEL_VS_CAPCOM_2" -G "$SCRIPT_DIR/IP.BIN" -joliet -rock -l -o "$TEMP_BUILD/data.iso" "$TEMP_BUILD/data"

echo "[*] Convirtiendo ISO a formato CDI..."
CDI4DC_EXE="$REPO_ROOT/Tools/BootDreams-1.06c/tools/cdi4dc.exe"
AUDIO_RAW="$REPO_ROOT/Tools/BootDreams-1.06c/tools/audio.raw"

if command -v wine &> /dev/null && [ -f "$CDI4DC_EXE" ]; then
    echo "    Utilizando cdi4dc vía Wine..."
    wine "$CDI4DC_EXE" "$TEMP_BUILD/data.iso" "$OUTPUT_CDI" 11702
elif command -v cdi4dc &> /dev/null; then
    echo "    Utilizando cdi4dc nativo de Linux..."
    cdi4dc "$TEMP_BUILD/data.iso" "$OUTPUT_CDI" 11702
else
    echo "[!] Nota: Para empaquetar el CDI final se necesita 'cdi4dc'."
    echo "    Puedes instalar Wine (sudo apt install wine) o compilar img4dc/cdi4dc en Linux."
    echo "    Se ha guardado la imagen ISO intermedia en: $OUTPUT_DIR/data.iso"
    cp "$TEMP_BUILD/data.iso" "$OUTPUT_DIR/data.iso"
    rm -rf "$TEMP_BUILD"
    exit 0
fi

rm -rf "$TEMP_BUILD"
echo ""
echo "[✓] ¡Imagen CDI generada con éxito!"
echo "    Ubicación: $OUTPUT_CDI"
echo "    Puedes quemarla en CD-R con ImgBurn / cdrecord o probarla en emuladores."
