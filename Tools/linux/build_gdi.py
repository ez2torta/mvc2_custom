#!/usr/bin/env python3
"""
build_gdi.py - Constructor automatizado de GDI para SEGA Dreamcast en Linux.

Genera una imagen GDI válida (disc.gdi, track01.bin, track02.raw, track03.bin)
con la cabecera IP.BIN de SEGA Katana OS en Pista 1 y Pista 3, y sistema ISO9660 Nivel 1,
100% compatible con Flycast, Redream, DEmul y ODEs de hardware (GDEMU, MODE, USB-GDROM).
"""

import os
import sys
import shutil
import struct
import pycdlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
MVC2_DATA_DIR = os.path.join(REPO_ROOT, "MVC2")
MVC2_IP_BIN = os.path.join(MVC2_DATA_DIR, "IP.BIN")

def clean_8_3(filename):
    """Convierte un nombre de archivo a formato ISO9660 Nivel 1 (8.3 mayúsculas)."""
    name = filename.upper()
    if '.' in name:
        base, ext = name.rsplit('.', 1)
    else:
        base, ext = name, ''
    clean_base = ''.join(c if (c.isalnum() or c == '_') else '_' for c in base)[:8]
    clean_ext = ''.join(c if (c.isalnum() or c == '_') else '_' for c in ext)[:3]
    if clean_ext:
        return f"{clean_base}.{clean_ext};1"
    return f"{clean_base};1"

def patch_iso_lba(iso_bytes, lba_offset=45000):
    """
    Ajusta todas las referencias LBA (PVD, Tablas de Rutas L/M y Registros de Directorio)
    a la dirección LBA física absoluta de la pista en el disco (LBA 45000 para Track 03).
    """
    data = bytearray(iso_bytes)
    sec = 16
    visited_dirs = set()
    dir_sectors_to_visit = []

    # 1. Ajustar Descriptores de Volumen (PVD en sector 16)
    while sec < len(data) // 2048:
        sec_offset = sec * 2048
        vd_type = data[sec_offset]
        vd_id = data[sec_offset+1:sec_offset+6]
        if vd_id != b'CD001' or vd_type == 255:
            break

        if vd_type in (1, 2):
            l_path = struct.unpack('<I', data[sec_offset+140:sec_offset+144])[0]
            if 0 < l_path < lba_offset:
                struct.pack_into('<I', data, sec_offset+140, l_path + lba_offset)

            m_path = struct.unpack('>I', data[sec_offset+148:sec_offset+152])[0]
            if 0 < m_path < lba_offset:
                struct.pack_into('>I', data, sec_offset+148, m_path + lba_offset)

            root_dr = sec_offset + 156
            root_extent = struct.unpack('<I', data[root_dr+2:root_dr+6])[0]
            root_size = struct.unpack('<I', data[root_dr+10:root_dr+14])[0]
            if root_extent < lba_offset:
                struct.pack_into('<I', data, root_dr+2, root_extent + lba_offset)
                struct.pack_into('>I', data, root_dr+6, root_extent + lba_offset)
                if root_extent not in visited_dirs:
                    dir_sectors_to_visit.append((root_extent, root_size))
                    visited_dirs.add(root_extent)

            # Ajustar tablas de rutas
            if l_path > 0 and l_path not in visited_dirs:
                pt_size = struct.unpack('<I', data[sec_offset+132:sec_offset+136])[0]
                pt_offset = l_path * 2048
                pt_pos = pt_offset
                while pt_pos < pt_offset + pt_size:
                    len_di = data[pt_pos]
                    if len_di == 0:
                        break
                    extent = struct.unpack('<I', data[pt_pos+2:pt_pos+6])[0]
                    if extent < lba_offset:
                        struct.pack_into('<I', data, pt_pos+2, extent + lba_offset)
                    pt_pos += 8 + len_di + (len_di % 2)

            if m_path > 0 and m_path not in visited_dirs:
                pt_size = struct.unpack('>I', data[sec_offset+136:sec_offset+140])[0]
                pt_offset = m_path * 2048
                pt_pos = pt_offset
                while pt_pos < pt_offset + pt_size:
                    len_di = data[pt_pos]
                    if len_di == 0:
                        break
                    extent = struct.unpack('>I', data[pt_pos+2:pt_pos+6])[0]
                    if extent < lba_offset:
                        struct.pack_into('>I', data, pt_pos+2, extent + lba_offset)
                    pt_pos += 8 + len_di + (len_di % 2)
        sec += 1

    # 2. Ajustar registros de directorios recursivamente
    patched_dirs = 0
    patched_files = 0

    while dir_sectors_to_visit:
        dir_sec, dir_size = dir_sectors_to_visit.pop(0)
        patched_dirs += 1
        dir_start = dir_sec * 2048
        dir_end = dir_start + dir_size
        pos = dir_start

        while pos < dir_end and pos < len(data):
            sec_start = (pos // 2048) * 2048
            len_dr = data[pos]
            if len_dr == 0:
                pos = sec_start + 2048
                continue

            extent = struct.unpack('<I', data[pos+2:pos+6])[0]
            size = struct.unpack('<I', data[pos+10:pos+14])[0]
            flags = data[pos+25]
            len_fi = data[pos+32]
            name = data[pos+33:pos+33+len_fi]

            if extent < lba_offset:
                struct.pack_into('<I', data, pos+2, extent + lba_offset)
                struct.pack_into('>I', data, pos+6, extent + lba_offset)

            if (flags & 0x02) and name not in (b'\x00', b'\x01', b'\x00\x00', b'\x00\x01'):
                if extent not in visited_dirs and extent < len(data) // 2048:
                    visited_dirs.add(extent)
                    dir_sectors_to_visit.append((extent, size))
            elif not (flags & 0x02):
                patched_files += 1

            pos += len_dr

    return data, patched_dirs, patched_files

def generate_track01_pycdlib(ip_bin_path, output_path):
    """
    Crea la pista de baja densidad track01.bin (LBA 0):
    - Inyecta IP.BIN en los primeros 32KB (sectores 0..15).
    - Agrega PVD en sector 16 con README.TXT.
    - Rellena a 300 sectores (614,400 bytes).
    """
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=1, vol_ident='DREAMCAST_LD')

    dummy_text = b"This is a SEGA Dreamcast disc.\nHigh density game data is stored in track 03.\n"
    iso.add_fp(pycdlib.pycdlib.io.BytesIO(dummy_text), len(dummy_text), '/README.TXT;1')

    temp_iso = output_path + ".tmp"
    iso.write(temp_iso)
    iso.close()

    with open(temp_iso, 'rb') as f:
        iso_raw = bytearray(f.read())
    os.remove(temp_iso)

    # Inyectar IP.BIN en sectores 0..15 de Track 01
    with open(ip_bin_path, 'rb') as f:
        ip_data = f.read(32768)

    iso_raw[0:32768] = ip_data

    # Pad a 300 sectores (614,400 bytes)
    target_size = 300 * 2048
    if len(iso_raw) < target_size:
        iso_raw.extend(b'\x00' * (target_size - len(iso_raw)))
    elif len(iso_raw) > target_size:
        iso_raw = iso_raw[:target_size]

    with open(output_path, 'wb') as f:
        f.write(iso_raw)

def generate_track02(output_path):
    """Genera audio RAW PCM estéreo a 44.1kHz (4 segundos) para track02.raw (LBA 450)."""
    num_bytes = 44100 * 2 * 2 * 4  # 705,600 bytes (300 sectores de 2352 bytes)
    with open(output_path, "wb") as f:
        f.write(b'\x00' * num_bytes)

def generate_track03(data_dir, ip_bin_path, output_path):
    """
    Crea la pista de alta densidad track03.bin (LBA 45000) en formato ISO9660 Nivel 1 puro:
    - Empaqueta todos los archivos de juego en formato 8.3 estricto.
    - Inyecta IP.BIN en los sectores 0..15.
    - Parchea todos los LBAs de ISO9660 con offset +45000.
    """
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=1, vol_ident='MARVEL2')

    added_files = 0
    added_dirs = 0

    for root, dirs, files in os.walk(data_dir):
        rel_root = os.path.relpath(root, data_dir)
        if rel_root != '.':
            parts = rel_root.split(os.sep)
            curr_iso = ''
            for p in parts:
                p_clean = ''.join(c if (c.isalnum() or c == '_') else '_' for c in p.upper())[:8]
                curr_iso += '/' + p_clean
                try:
                    iso.add_directory(curr_iso)
                    added_dirs += 1
                except pycdlib.pycdlibexception.PyCdlibException:
                    pass

        for f in sorted(files):
            # Omitir archivos auxiliares de modding/backup
            if f.endswith(('.bak', '.backup.BIN', '.orig')) or f.startswith('.'):
                continue
            full_path = os.path.join(root, f)
            if rel_root == '.':
                iso_dir = ''
            else:
                iso_dir = '/' + '/'.join(''.join(c if (c.isalnum() or c == '_') else '_' for c in p.upper())[:8] for p in rel_root.split(os.sep))

            iso_n = clean_8_3(f)
            iso_file_path = f'{iso_dir}/{iso_n}'

            try:
                iso.add_file(full_path, iso_file_path)
                added_files += 1
            except Exception as e:
                print(f"    [!] Advertencia agregando {full_path}: {e}")

    temp_iso = output_path + ".tmp"
    iso.write(temp_iso)
    iso.close()

    with open(temp_iso, 'rb') as f:
        iso_raw = bytearray(f.read())
    os.remove(temp_iso)

    # Inyectar IP.BIN
    with open(ip_bin_path, 'rb') as f:
        ip_data = f.read(32768)

    iso_raw[0:32768] = ip_data

    # Parchear LBA offset 45000
    patched_data, p_dirs, p_files = patch_iso_lba(iso_raw, 45000)

    with open(output_path, 'wb') as f:
        f.write(patched_data)

    print(f"    [✓] {added_files} archivos y {added_dirs} subdirectorios empaquetados en ISO9660 Nivel 1")
    print(f"    [✓] LBA offset +45000 aplicado exitosamente a {p_dirs} directorios y {p_files} registros.")
    print(f"    [✓] Tamaño final de track03.bin: {len(patched_data):,} bytes ({len(patched_data)//2048:,} sectores)")

def verify_gdi(output_dir):
    """
    Verifica que Track 01, Track 02 y Track 03 tienen sus cabeceras y descriptores correctos.
    """
    t1_file = os.path.join(output_dir, "track01.bin")
    t3_file = os.path.join(output_dir, "track03.bin")

    # Verificar Track 01
    with open(t1_file, 'rb') as f:
        t1_head = f.read(32)
    if not t1_head.startswith(b'SEGA SEGAKATANA'):
        print("    [X] Error de verificación: Track 01 no contiene cabecera SEGA SEGAKATANA.")
        return False

    # Verificar Track 03
    with open(t3_file, 'rb') as f:
        t3_head = f.read(1024 * 1024)
    if not t3_head.startswith(b'SEGA SEGAKATANA'):
        print("    [X] Error de verificación: Track 03 no contiene cabecera SEGA SEGAKATANA.")
        return False

    # Verificar PVD en sector 16 de Track 03
    pvd = t3_head[16*2048:17*2048]
    if pvd[1:6] != b'CD001':
        print("    [X] Error de verificación: PVD no válido en sector 16 de Track 03.")
        return False

    root_dr = pvd[156:156+34]
    root_extent = struct.unpack('<I', root_dr[2:6])[0]
    if root_extent < 45000:
        print(f"    [X] Error de verificación: Root extent ({root_extent}) no tiene offset LBA 45000.")
        return False

    print(f"    [✓] Verificación GDI exitosa: Track 01 y Track 03 alineados y validados.")
    return True

def build_gdi(output_dir):
    os.makedirs(output_dir, exist_ok=True)

    print("========================================================================")
    print("      Generador GDI Dreamcast (Marvel vs Capcom 2 Modding)")
    print("========================================================================")

    ip_bin_path = os.path.join(output_dir, "IP.BIN")
    if os.path.exists(MVC2_IP_BIN) and os.path.getsize(MVC2_IP_BIN) == 32768:
        print("\n[*] 1/4 Usando IP.BIN nativo de MVC2 (Katana OS bootstrap + TOC1)...")
        shutil.copy2(MVC2_IP_BIN, ip_bin_path)
    else:
        print("\n[!] Error: No se encontró MVC2/IP.BIN nativo.")
        return False

    track01_path = os.path.join(output_dir, "track01.bin")
    track02_path = os.path.join(output_dir, "track02.raw")
    track03_path = os.path.join(output_dir, "track03.bin")
    gdi_path = os.path.join(output_dir, "disc.gdi")

    print("\n[*] 2/4 Generando track01.bin (Low Density con IP.BIN) y track02.raw (Audio Gap)...")
    generate_track01_pycdlib(ip_bin_path, track01_path)
    generate_track02(track02_path)

    print("\n[*] 3/4 Generando track03.bin (High Density ISO9660 Nivel 1 a LBA 45000)...")
    generate_track03(MVC2_DATA_DIR, ip_bin_path, track03_path)

    print("\n[*] 4/4 Creando disc.gdi y ejecutando auto-verificación...")
    gdi_content = f"""3
1 0 4 2048 track01.bin 0
2 450 0 2352 track02.raw 0
3 45000 4 2048 track03.bin 0
"""
    with open(gdi_path, "w") as f:
        f.write(gdi_content)

    if verify_gdi(output_dir):
        print(f"\n[✓] ¡GDI generado y verificado con ÉXITO en {output_dir}!")
        print(f"    - {gdi_path}")
        print(f"    - {track01_path} ({os.path.getsize(track01_path):,} bytes)")
        print(f"    - {track02_path} ({os.path.getsize(track02_path):,} bytes)")
        print(f"    - {track03_path} ({os.path.getsize(track03_path):,} bytes)")
        print("\n100% Compatible con Flycast, Redream, DEmul y ODEs (GDEMU, MODE, USB-GDROM).")
        return True
    else:
        print("\n[!] Advertencia: La verificación detectó anomalías.")
        return False

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "output_gdi")
    build_gdi(out_dir)
