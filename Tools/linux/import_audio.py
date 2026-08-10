#!/usr/bin/env python3
"""
import_audio.py - Reinyecta archivos de audio (WAV, MP3, FLAC, OGG) a formato CRI ADX
en la carpeta de datos del juego MVC2/.
"""

import os
import sys
import subprocess
import shutil
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
MVC2_DIR = os.path.join(REPO_ROOT, "MVC2")
DEFAULT_IN_DIR = os.path.join(REPO_ROOT, "Extracted_Audio")

def convert_to_adx(input_audio_path, output_adx_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_audio_path,
        "-ar", "44100",
        "-ac", "2",
        "-c:a", "adx",
        output_adx_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0

def import_all_audio(input_dir, mvc2_dir):
    if not shutil.which("ffmpeg"):
        print("[!] Error: 'ffmpeg' no está instalado en el sistema.")
        print("    Instálalo con: sudo apt install ffmpeg")
        sys.exit(1)

    print("=======================================================")
    print("    MVC2 Audio Injector (WAV/MP3 -> CRI ADX)")
    print(f"    Origen : {input_dir}")
    print(f"    Destino: {mvc2_dir}")
    print("=======================================================\n")

    os.makedirs(mvc2_dir, exist_ok=True)

    # Buscar archivos de audio en input_dir (o en subcarpetas WAV/ / MP3/)
    search_dirs = [input_dir]
    if os.path.exists(os.path.join(input_dir, "WAV")):
        search_dirs.append(os.path.join(input_dir, "WAV"))
    if os.path.exists(os.path.join(input_dir, "MP3")):
        search_dirs.append(os.path.join(input_dir, "MP3"))

    processed_keys = set()
    total_injected = 0

    # Patrón para detectar el prefijo ADX_XXXX
    pattern = re.compile(r"^(ADX_[0-9A-Z]{4})", re.IGNORECASE)

    for d in search_dirs:
        for fname in sorted(os.listdir(d)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in [".wav", ".mp3", ".flac", ".ogg", ".aiff", ".m4a"]:
                continue

            match = pattern.match(fname)
            if not match:
                continue

            adx_key = match.group(1).upper()
            if adx_key in processed_keys:
                continue # Ya procesado con mayor prioridad (ej. WAV sobre MP3)

            target_filename = f"{adx_key}.BIN"
            src_file = os.path.join(d, fname)
            dest_file = os.path.join(mvc2_dir, target_filename)

            if convert_to_adx(src_file, dest_file):
                print(f"[✓] {fname} -> {target_filename}")
                processed_keys.add(adx_key)
                total_injected += 1
            else:
                print(f"[!] Error convirtiendo {fname}")

    print("\n=======================================================")
    print(f"[✓] ¡Inyección de audio completada!")
    print(f"    Pistas actualizadas: {total_injected}")
    print(f"    Carpeta destino: {mvc2_dir}")
    print("=======================================================")

if __name__ == "__main__":
    in_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IN_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else MVC2_DIR
    import_all_audio(in_dir, out_dir)
