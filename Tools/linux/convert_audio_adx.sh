#!/bin/bash
# ==============================================================================
# convert_audio_adx.sh - Convierte pistas de audio a CRI ADX para Dreamcast
# Utiliza FFmpeg directamente en Linux (sin necesidad de radx_encode en Windows)
# ==============================================================================

if [ "$#" -lt 1 ]; then
    echo "Uso: $0 <archivo_audio_origen> [archivo_adx_destino]"
    echo "Ejemplo: $0 mi_cancion.mp3 ADX_S000.BIN"
    exit 1
fi

INPUT="$1"
OUTPUT="${2:-${INPUT%.*}.adx}"

if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg no está instalado en el sistema."
    echo "Instálalo con: sudo apt install ffmpeg"
    exit 1
fi

echo "[*] Convirtiendo '$INPUT' a formato CRI ADX (44100Hz Stereo)..."
ffmpeg -y -i "$INPUT" -ar 44100 -ac 2 -c:a adx "$OUTPUT"

if [ $? -eq 0 ]; then
    echo "[✓] Archivo generado exitosamente: $OUTPUT"
    echo "Recuerda colocarlo en la carpeta MVC2/ con el nombre correspondiente (ej. ADX_S000.BIN, ADX_OPEN.BIN, etc.)"
else
    echo "[!] Error durante la conversión."
    exit 1
fi
