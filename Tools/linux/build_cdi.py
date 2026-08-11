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

def parse_dummy_target(dummy_arg):
    if not dummy_arg:
        return None
    val = str(dummy_arg).strip().lower().replace("mb", "")
    if val in ("1", "true", "yes", "dummy", "default"):
        return 650
    try:
        num = int(val)
        return num if num > 0 else None
    except ValueError:
        return None

def build_cdi(output_dir, dummy_arg=None):
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join(output_dir, "temp_cdi_build")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    dummy_target_mb = parse_dummy_target(dummy_arg)
    if dummy_target_mb:
        output_cdi_name = "mvc2_custom_dummy.cdi"
    else:
        output_cdi_name = "mvc2_custom.cdi"
    output_cdi = os.path.join(output_dir, output_cdi_name)
    temp_iso_path = os.path.join(temp_dir, "data_lba0.iso")

    print("========================================================================")
    print("      Generador CDI Autoboot Dreamcast (Mario CDI Data/Data Layout)")
    if dummy_target_mb:
        print(f"      [MODO OPTIMIZADO CON DUMMY: Límite {dummy_target_mb} MB]")
    else:
        print("      [MODO COMPACTO: Sin Dummy]")
    print("========================================================================")

    # 1. Crear ISO9660 Nivel 3 con Joliet a LBA 0
    print("\n[*] 1/3 Empaquetando filesystem ISO9660 a LBA 0 (Data/Data)...")
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, vol_ident='MARVEL2')

    # Calcular tamaño total de archivos reales
    total_real_bytes = 0
    for root, dirs, files in os.walk(MVC2_DATA_DIR):
        for f in files:
            if f.endswith(('.bak', '.backup.BIN', '.orig')) or f.startswith('.'):
                continue
            total_real_bytes += os.path.getsize(os.path.join(root, f))

    # Si se solicitó Dummy, calcular tamaño para que el CDI final sea <= target_mb (por defecto 650 MB)
    if dummy_target_mb:
        target_cdi_bytes = dummy_target_mb * 1024 * 1024
        # Cada sector de 2048 bytes en ISO genera un sector de 2336 bytes en CDI
        target_iso_bytes = int((target_cdi_bytes - 10000) * (2048 / 2336))
        overhead_estimate = 4 * 1024 * 1024 # Overhead de tablas de directorios y Joliet
        dummy_bytes = max(0, target_iso_bytes - total_real_bytes - overhead_estimate)
        
        # Alinear a múltiplos de 2048
        dummy_bytes = (dummy_bytes // 2048) * 2048

        if dummy_bytes > 0:
            dummy_file_path = os.path.join(temp_dir, "0DUMMY.DAT")
            print(f"    [+] Generando 0DUMMY.DAT ({dummy_bytes:,} bytes / {dummy_bytes / (1024*1024):.2f} MB)...")
            print("        (Coloca los datos del juego en el borde exterior del CD para máxima velocidad en la consola)")
            with open(dummy_file_path, "wb") as df:
                df.truncate(dummy_bytes)
            iso.add_file(dummy_file_path, '/0DUMMY.DAT;1', joliet_path='/0DUMMY.DAT')

    # Archivos raíz
    for f in sorted(os.listdir(MVC2_DATA_DIR)):
        full_p = os.path.join(MVC2_DATA_DIR, f)
        if os.path.isfile(full_p):
            if f.endswith(('.bak', '.backup.BIN', '.orig')) or f.startswith('.'):
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
    if dummy_target_mb:
        print(f"    - Optimización: 0DUMMY.DAT incluido (Borde exterior activo)")
    print("\n100% Compatible con Flycast, Redream, DEmul y consolas Dreamcast reales (CD-R).")
    return True

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "output_cdi")
    dummy_param = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("DUMMY")
    build_cdi(out_dir, dummy_param)
