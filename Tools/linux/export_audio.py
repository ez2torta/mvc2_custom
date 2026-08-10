#!/usr/bin/env python3
"""
export_audio.py - Extrae todas las pistas de audio CRI ADX de Marvel vs Capcom 2
a formatos WAV (lossless) y MP3 (320kbps con metadatos ID3).
"""

import os
import sys
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
MVC2_DIR = os.path.join(REPO_ROOT, "MVC2")
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, "Extracted_Audio")

# Mapa de nombres descriptivos para cada archivo ADX
SONG_TITLES = {
    "ADX_S000.BIN": ("Air Ship (Day)", "Stage Theme"),
    "ADX_S010.BIN": ("Desert (Sunset)", "Stage Theme"),
    "ADX_S020.BIN": ("Factory", "Stage Theme"),
    "ADX_S030.BIN": ("Carnival (Spring)", "Stage Theme"),
    "ADX_S040.BIN": ("Swamp", "Stage Theme"),
    "ADX_S050.BIN": ("Cave (Water)", "Stage Theme"),
    "ADX_S060.BIN": ("Clock Tower (Clear)", "Stage Theme"),
    "ADX_S070.BIN": ("River (Ice)", "Stage Theme"),
    "ADX_S080.BIN": ("Abyss 1 (Armor)", "Boss Theme"),
    "ADX_S090.BIN": ("Abyss 2 (Form 2)", "Boss Theme"),
    "ADX_S0A0.BIN": ("Abyss 3 (Giant)", "Boss Theme"),
    "ADX_S0B0.BIN": ("Training Stage", "Training Theme"),
    "ADX_S0C0.BIN": ("Alternate Carnival (Winter)", "Stage Theme"),
    "ADX_S0D0.BIN": ("Alternate Swamp (Asian)", "Stage Theme"),
    "ADX_S0E0.BIN": ("Alternate Cave (Lava)", "Stage Theme"),
    "ADX_S0F0.BIN": ("Alternate Clock (Snowy)", "Stage Theme"),
    "ADX_S100.BIN": ("Alternate River (Raft)", "Stage Theme"),
    "ADX_S110.BIN": ("Shuffle Stage 17", "Custom Stage Theme"),
    "ADX_S120.BIN": ("Shuffle Stage 18", "Custom Stage Theme"),
    "ADX_S130.BIN": ("Shuffle Stage 19", "Custom Stage Theme"),
    "ADX_S140.BIN": ("Shuffle Stage 20", "Custom Stage Theme"),
    "ADX_S150.BIN": ("Shuffle Stage 21", "Custom Stage Theme"),
    "ADX_S160.BIN": ("Shuffle Stage 22", "Custom Stage Theme"),
    "ADX_S170.BIN": ("Shuffle Stage 23", "Custom Stage Theme"),
    "ADX_S180.BIN": ("Shuffle Stage 24", "Custom Stage Theme"),
    "ADX_S190.BIN": ("Shuffle Stage 25", "Custom Stage Theme"),
    "ADX_S1A0.BIN": ("Shuffle Stage 26", "Custom Stage Theme"),
    "ADX_S1B0.BIN": ("Shuffle Stage 27", "Custom Stage Theme"),
    "ADX_S1C0.BIN": ("Shuffle Stage 28", "Custom Stage Theme"),
    "ADX_S1D0.BIN": ("Shuffle Stage 29", "Custom Stage Theme"),
    "ADX_S1E0.BIN": ("Shuffle Stage 30", "Custom Stage Theme"),
    "ADX_S1F0.BIN": ("Shuffle Stage 31", "Custom Stage Theme"),
    "ADX_OPEN.BIN": ("Opening Movie", "Cinematic Theme"),
    "ADX_STAF.BIN": ("Staff Roll (Credits)", "Credits Theme"),
    "ADX_CAPL.BIN": ("Capcom Logo", "Jingle"),
    "ADX_SELC.BIN": ("Character Select", "Menu Theme"),
    "ADX_CONT.BIN": ("Continue Screen", "Menu Theme"),
    "ADX_HERE.BIN": ("Here Comes a New Challenger", "Jingle"),
    "ADX_OVER.BIN": ("Game Over", "Jingle"),
    "ADX_RANK.BIN": ("Ranking Screen", "Menu Theme"),
    "ADX_WINS.BIN": ("Win Screen", "Victory Theme"),
    "ADX_MENU.BIN": ("Main Menu", "Menu Theme"),
    "ADX_NETW.BIN": ("Network Menu", "Menu Theme"),
    "ADX_NSHP.BIN": ("Alternate Ship (Night)", "Stage Theme"),
    "ADX_NDST.BIN": ("Alternate Desert (Blue Sky)", "Stage Theme"),
    "ADX_NCRN.BIN": ("Alternate Carnival", "Stage Theme"),
    "ADX_NSWP.BIN": ("Alternate Swamp", "Stage Theme"),
    "ADX_NCAV.BIN": ("Alternate Cave", "Stage Theme"),
    "ADX_NCLK.BIN": ("Alternate Clock", "Stage Theme"),
    "ADX_NRFT.BIN": ("Alternate River", "Stage Theme"),
}

def export_all_audio(mvc2_dir, out_dir):
    if not shutil.which("ffmpeg"):
        print("[!] Error: 'ffmpeg' no está instalado en el sistema.")
        print("    Instálalo con: sudo apt install ffmpeg")
        sys.exit(1)

    wav_dir = os.path.join(out_dir, "WAV")
    mp3_dir = os.path.join(out_dir, "MP3")
    os.makedirs(wav_dir, exist_ok=True)
    os.makedirs(mp3_dir, exist_ok=True)

    print("=======================================================")
    print("    MVC2 Audio Extractor (ADX -> WAV & MP3)")
    print(f"    Origen : {mvc2_dir}")
    print(f"    Destino: {out_dir}")
    print("=======================================================\n")

    files = sorted([f for f in os.listdir(mvc2_dir) if f.upper().startswith("ADX_") and f.upper().endswith(".BIN")])
    if not files:
        print(f"[!] No se encontraron archivos ADX_*.BIN en {mvc2_dir}")
        return

    tracklist_md = os.path.join(out_dir, "TRACK_LIST.md")
    md_lines = [
        "# Lista de Pistas de Audio de Marvel vs Capcom 2",
        "",
        "| Archivo en el Juego | Título Descriptivo | Tipo | Archivo WAV | Archivo MP3 |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    total_exported = 0
    for filename in files:
        base_id = filename.replace(".BIN", "")
        title, track_type = SONG_TITLES.get(filename, (base_id, "Music"))
        
        # Limpiar nombre para archivo
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in title).replace(" ", "_")
        wav_filename = f"{base_id}_{safe_title}.wav"
        mp3_filename = f"{base_id}_{safe_title}.mp3"
        
        in_path = os.path.join(mvc2_dir, filename)
        wav_path = os.path.join(wav_dir, wav_filename)
        mp3_path = os.path.join(mp3_dir, mp3_filename)

        # 1. Exportar WAV (PCM 16-bit 44.1kHz Stereo)
        cmd_wav = ["ffmpeg", "-y", "-i", in_path, "-c:a", "pcm_s16le", wav_path]
        subprocess.run(cmd_wav, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 2. Exportar MP3 con metadatos ID3
        cmd_mp3 = [
            "ffmpeg", "-y", "-i", in_path,
            "-b:a", "320k",
            "-metadata", f"title={title}",
            "-metadata", "artist=Capcom Sound Team",
            "-metadata", "album=Marvel vs Capcom 2 (Dreamcast)",
            "-metadata", f"genre={track_type}",
            mp3_path
        ]
        subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        md_lines.append(f"| `{filename}` | **{title}** | {track_type} | [`WAV/{wav_filename}`](file://{wav_path}) | [`MP3/{mp3_filename}`](file://{mp3_path}) |")
        print(f"[✓] {filename} -> {title} ({wav_filename})")
        total_exported += 1

    with open(tracklist_md, "w") as f:
        f.write("\n".join(md_lines) + "\n")

    print("\n=======================================================")
    print(f"[✓] ¡Extracción de audio completada!")
    print(f"    Pistas procesadas: {total_exported}")
    print(f"    Archivos WAV: {wav_dir}")
    print(f"    Archivos MP3: {mp3_dir}")
    print(f"    Índice: {tracklist_md}")
    print("=======================================================")

if __name__ == "__main__":
    in_dir = sys.argv[1] if len(sys.argv) > 1 else MVC2_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    export_all_audio(in_dir, out_dir)
