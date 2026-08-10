#!/usr/bin/env python3
"""
build_gdi.py - Constructor automatizado de GDI para SEGA Dreamcast en Linux.

Genera una imagen GDI válida (disc.gdi, track01.bin, track02.raw, track03.bin)
a partir de la carpeta de datos del juego (ej. MVC2/).
"""

import os
import sys
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
MVC2_DATA_DIR = os.path.join(REPO_ROOT, "MVC2")
IP_TEMPLATE = os.path.join(REPO_ROOT, "Tools/BootDreams-1.06c/tools/IP.BIN")

def check_dependencies():
    tools = ["genisoimage", "mkisofs", "xorrisofs"]
    found_iso_tool = None
    for t in tools:
        if shutil.which(t):
            found_iso_tool = t
            break
    
    if not found_iso_tool:
        print("[!] Advertencia: No se encontró 'genisoimage' o 'mkisofs' en tu sistema.")
        print("    Para instalar en Ubuntu/Debian ejecuta:")
        print("    sudo apt update && sudo apt install genisoimage")
        return None
    return found_iso_tool

def generate_track01(iso_tool, output_path):
    """Crea una pista de baja densidad básica para track01.bin"""
    dummy_dir = "/tmp/dc_dummy_track01"
    os.makedirs(dummy_dir, exist_ok=True)
    readme_path = os.path.join(dummy_dir, "README.TXT")
    with open(readme_path, "w") as f:
        f.write("This is a SEGA Dreamcast disc.\nHigh density data is in track 03.\n")
    
    cmd = [
        iso_tool,
        "-V", "DREAMCAST_LD",
        "-joliet", "-rock", "-l",
        "-o", output_path,
        dummy_dir
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    shutil.rmtree(dummy_dir)

def generate_track02(output_path):
    """Genera 4 segundos de audio RAW PCM (44.1kHz 16-bit stereo) para track02.raw"""
    # 44100 muestras/seg * 2 canales * 2 bytes/muestra * 4 segundos = ~705600 bytes
    num_bytes = 44100 * 2 * 2 * 4
    with open(output_path, "wb") as f:
        f.write(b'\x00' * num_bytes)

def build_gdi(output_dir):
    iso_tool = check_dependencies()
    if not iso_tool:
        return False

    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Generar IP.BIN
    ip_bin_path = os.path.join(output_dir, "IP.BIN")
    from make_ipbin import create_custom_ipbin
    create_custom_ipbin(IP_TEMPLATE, ip_bin_path, title="MARVEL VS. CAPCOM 2", bootfile="1ST_READ.BIN", is_gdi=True)

    track01_path = os.path.join(output_dir, "track01.bin")
    track02_path = os.path.join(output_dir, "track02.raw")
    track03_path = os.path.join(output_dir, "track03.bin")
    gdi_path = os.path.join(output_dir, "disc.gdi")

    print("\n[*] 1/4 Generando track01.bin (Low Density Data)...")
    generate_track01(iso_tool, track01_path)

    print("[*] 2/4 Generando track02.raw (Audio Dummy)...")
    generate_track02(track02_path)

    print("[*] 3/4 Generando track03.bin (High Density Game Data a LBA 45000)...")
    cmd_track03 = [
        iso_tool,
        "-C", "0,45000",
        "-V", "MARVEL_VS_CAPCOM_2",
        "-G", ip_bin_path,
        "-joliet", "-rock", "-l",
        "-o", track03_path,
        MVC2_DATA_DIR
    ]
    res = subprocess.run(cmd_track03)
    if res.returncode != 0:
        print("[!] Error generando track03.bin")
        return False

    print("[*] 4/4 Creando disc.gdi...")
    # Calcular tamaños en sectores (2048 para data, 2352 para raw)
    track01_sectors = os.path.getsize(track01_path) // 2048
    gdi_content = f"""3
1 0 4 2048 track01.bin 0
2 450 0 2352 track02.raw 0
3 45000 4 2048 track03.bin 0
"""
    with open(gdi_path, "w") as f:
        f.write(gdi_content)

    print(f"\n[✓] ¡GDI generado con éxito en {output_dir}!")
    print(f"    - {gdi_path}")
    print(f"    - {track01_path}")
    print(f"    - {track02_path}")
    print(f"    - {track03_path}")
    print("\nPuedes cargarlo directamente en Flycast, Redream o copiarlo a tu SD de GDEMU.")
    return True

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "output_gdi")
    build_gdi(out_dir)
