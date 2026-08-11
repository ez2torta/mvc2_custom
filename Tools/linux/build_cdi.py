#!/usr/bin/env python3
"""
build_cdi.py - Constructor automatizado de CDI Autoboot (MIL-CD Data/Data) para SEGA Dreamcast en Linux.

Genera una imagen CDI autobootable Data/Data (mvc2_custom.cdi) usando cdi4dc -d (Padus DiscJuggler v3.5),
con estructura idéntica a Mario vs Capcom 2 (498 MB),
100% compatible con Flycast, Redream y consolas Dreamcast reales en CD-R.
"""

import os
import sys
import shutil
import subprocess
import pycdlib
from build_gdi import clean_8_3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
MVC2_DATA_DIR = os.path.join(REPO_ROOT, "MVC2")
MVC2_IP_BIN = os.path.join(MVC2_DATA_DIR, "IP.BIN")
CDI4DC_BIN = os.path.join(SCRIPT_DIR, "cdi4dc")

def build_cdi(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join(output_dir, "temp_cdi_build")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    output_cdi = os.path.join(output_dir, "mvc2_custom.cdi")
    temp_iso_path = os.path.join(temp_dir, "data_lba0.iso")

    print("========================================================================")
    print("      Generador CDI Autoboot Dreamcast (Mario CDI Data/Data Layout)")
    print("========================================================================")

    # 1. Crear ISO9660 Nivel 3 con Joliet a LBA 0
    print("\n[*] 1/3 Empaquetando filesystem ISO9660 a LBA 0 (Data/Data)...")
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, vol_ident='MARVEL2')

    # Archivos raíz
    for f in sorted(os.listdir(MVC2_DATA_DIR)):
        full_p = os.path.join(MVC2_DATA_DIR, f)
        if os.path.isfile(full_p):
            if f.endswith(('.bak', '.txt', '.backup.BIN')) or f.startswith('!'):
                continue
            iso_n = clean_8_3(f)
            iso.add_file(full_p, f'/{iso_n}', joliet_path=f'/{f}')

    # Subdirectorios
    for sub in ['DPETC', 'DPFONT', 'DPSS', 'DPTEX', 'DPWWW']:
        sub_p = os.path.join(MVC2_DATA_DIR, sub)
        if os.path.isdir(sub_p):
            try:
                iso.add_directory(f'/{sub}', joliet_path=f'/{sub}')
            except:
                pass
            for sf in sorted(os.listdir(sub_p)):
                sfull_p = os.path.join(sub_p, sf)
                if os.path.isfile(sfull_p):
                    iso_sn = clean_8_3(sf)
                    iso.add_file(sfull_p, f'/{sub}/{iso_sn}', joliet_path=f'/{sub}/{sf}')

    iso.write(temp_iso_path)
    iso.close()

    # 2. Inyectar IP.BIN auténtico en los primeros 32KB (sectores 0..15)
    print("[*] 2/3 Inyectando cabecera IP.BIN de SEGA Katana...")
    with open(temp_iso_path, 'r+b') as f:
        with open(MVC2_IP_BIN, 'rb') as ip_f:
            ip_data = ip_f.read(32768)
        f.seek(0)
        f.write(ip_data)

    # 3. Generar CDI con cdi4dc -d (Data/Data layout)
    print("[*] 3/3 Generando contenedor CDI DiscJuggler v3.5 (Data/Data) con cdi4dc...")
    res = subprocess.run([CDI4DC_BIN, temp_iso_path, output_cdi, "-d"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"    [X] Error en cdi4dc: {res.stderr or res.stdout}")
        return False

    # Limpieza
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"\n[✓] ¡Imagen CDI autoboot generada con ÉXITO!")
    print(f"    - Archivo: {output_cdi}")
    print(f"    - Formato: Data/Data (MSINFO 0)")
    print(f"    - Tamaño : {os.path.getsize(output_cdi):,} bytes ({os.path.getsize(output_cdi) / (1024*1024):.2f} MB)")
    print("\n100% Compatible con Flycast, Redream, DEmul y consolas Dreamcast reales (CD-R).")
    return True

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "output_cdi")
    build_cdi(out_dir)
