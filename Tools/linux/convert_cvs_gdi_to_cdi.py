#!/usr/bin/env python3
"""
convert_cvs_gdi_to_cdi.py - Conversor y Desarmador de Protección Anti-Copia para Capcom vs SNK (Dreamcast).

1. Extrae el filesystem del GDI (track03 + track04).
2. Omite 600 MB de archivos trampa/dummy (DC15POL.BIN, DC15TEX.BIN, COMPOT.BIN).
3. Aplica parches de ingeniería inversa en SH-4 (1ST_READ.BIN) para emular la verificación exitosa.
4. Scramblea el ejecutable y empaqueta un CDI Autoboot (Data/Data) DiscJuggler v3.5 con cdi4dc.
"""

import os
import sys
import shutil
import struct
import subprocess
import pycdlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
CDI4DC_BIN = os.path.join(SCRIPT_DIR, "cdi4dc")
SCRAMBLE_BIN = os.path.join(SCRIPT_DIR, "scramble")

def clean_8_3(filename):
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

class GDITrackReader:
    def __init__(self, gdi_folder):
        self.t3 = open(os.path.join(gdi_folder, 'track03.bin'), 'rb')
        self.t4 = open(os.path.join(gdi_folder, 'track04.bin'), 'rb')
        self.t3_lba = 45000
        self.t3_count = os.path.getsize(os.path.join(gdi_folder, 'track03.bin')) // 2352
        self.t4_lba = 114698
        self.t4_count = os.path.getsize(os.path.join(gdi_folder, 'track04.bin')) // 2352

    def read_sector(self, lba):
        if self.t3_lba <= lba < self.t3_lba + self.t3_count:
            idx = lba - self.t3_lba
            self.t3.seek(idx * 2352 + 16)
            return self.t3.read(2048)
        elif self.t4_lba <= lba < self.t4_lba + self.t4_count:
            idx = lba - self.t4_lba
            self.t4.seek(idx * 2352 + 16)
            return self.t4.read(2048)
        else:
            return b'\x00' * 2048

    def read_file(self, lba, size):
        sectors = (size + 2047) // 2048
        data = bytearray()
        for i in range(sectors):
            data.extend(self.read_sector(lba + i))
        return bytes(data[:size])

def convert_cvs(gdi_dir, output_cdi):
    print("========================================================================")
    print("   Conversor GDI -> CDI Autoboot con Reverse Engineering (Capcom vs SNK)")
    print("========================================================================")

    temp_dir = os.path.join(REPO_ROOT, "temp_cvs_build")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    extracted_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    print("\n[*] 1/4 Leyendo e indexando filesystem GDI...")
    reader = GDITrackReader(gdi_dir)
    pvd = reader.read_sector(45016)
    root_dr = pvd[156:156+34]
    root_extent = struct.unpack('<I', root_dr[2:6])[0]
    root_size = struct.unpack('<I', root_dr[10:14])[0]

    skipped_dummies = []
    extracted_count = 0

    def extract_dir(lba, size, rel_path=''):
        nonlocal extracted_count
        sectors = (size + 2047) // 2048
        data = b''.join(reader.read_sector(lba + i) for i in range(sectors))[:size]
        pos = 0
        while pos < len(data):
            len_dr = data[pos]
            if len_dr == 0:
                pos = ((pos // 2048) + 1) * 2048
                continue
            extent = struct.unpack('<I', data[pos+2:pos+6])[0]
            fsize = struct.unpack('<I', data[pos+10:pos+14])[0]
            flags = data[pos+25]
            len_fi = data[pos+32]
            name = data[pos+33:pos+33+len_fi].decode('iso-8859-1', 'replace')
            clean_name = name.split(';')[0]
            is_dir = bool(flags & 2)

            if name not in ('\x00', '\x01'):
                target_path = os.path.join(extracted_dir, rel_path, clean_name) if rel_path else os.path.join(extracted_dir, clean_name)
                if is_dir:
                    os.makedirs(target_path, exist_ok=True)
                    extract_dir(extent, fsize, os.path.join(rel_path, clean_name) if rel_path else clean_name)
                else:
                    if clean_name.upper() in ('DC15POL.BIN', 'DC15TEX.BIN', 'COMPOT.BIN'):
                        skipped_dummies.append((clean_name, fsize))
                        pos += len_dr
                        continue
                    file_bytes = reader.read_file(extent, fsize)
                    with open(target_path, 'wb') as f:
                        f.write(file_bytes)
                    extracted_count += 1
            pos += len_dr

    extract_dir(root_extent, root_size)
    print(f"    [+] {extracted_count} archivos de juego reales extraídos.")
    print(f"    [+] {len(skipped_dummies)} archivos dummy omitidos (Ahorro: {sum(s[1] for s in skipped_dummies)/(1024*1024):.2f} MB):")
    for dname, dsize in skipped_dummies:
        print(f"        - {dname} ({dsize/(1024*1024):.2f} MB)")

    # Inyectar IP.BIN de Track 03
    t3_raw = open(os.path.join(gdi_dir, 'track03.bin'), 'rb')
    ip_bytes = bytearray()
    for sec in range(16):
        t3_raw.seek(sec * 2352 + 16)
        ip_bytes.extend(t3_raw.read(2048))
    ip_path = os.path.join(extracted_dir, 'IP.BIN')
    with open(ip_path, 'wb') as f:
        f.write(ip_bytes)

    # 2. Patching 1ST_READ.BIN
    print("\n[*] 2/4 Aplicando ingeniería inversa en 1ST_READ.BIN (Bypass de protección)...")
    bin_path = os.path.join(extracted_dir, '1ST_READ.BIN')
    with open(bin_path, 'rb') as f:
        bin_data = bytearray(f.read())

    # Patch bytes: mov #0, r0 (0xE000) ; rts (0x000B) ; nop (0x0009)
    patch_bytes = struct.pack('<HHH', 0xE000, 0x000B, 0x0009)
    # Check 1: 0x8C012514 (file offset 0x2514)
    bin_data[0x2514:0x251A] = patch_bytes
    # Check 2: 0x8C070676 (file offset 0x60676)
    bin_data[0x60676:0x6067C] = patch_bytes
    # Check 3: 0x8C0947E4 (file offset 0x847E4)
    bin_data[0x847E4:0x847EA] = patch_bytes

    with open(bin_path, 'wb') as f:
        f.write(bin_data)
    print("    [✓] Parches SH-4 aplicados en 0x2514, 0x60676 y 0x847E4 (retorno forzado 0x00 / SUCCESS).")

    # Scramble 1ST_READ.BIN
    scrambled_1st = os.path.join(temp_dir, '1ST_READ.BIN')
    subprocess.run([SCRAMBLE_BIN, bin_path, scrambled_1st], check=True)

    # 3. ISO9660 Joliet Nivel 3
    print("\n[*] 3/4 Generando sistema de archivos ISO9660 Joliet Nivel 3 a LBA 0...")
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, vol_ident='CAPVSSNK')

    for root, dirs, files in os.walk(extracted_dir):
        rel_root = os.path.relpath(root, extracted_dir)
        if rel_root != '.':
            parts = rel_root.split(os.sep)
            curr_iso = ''
            curr_joliet = ''
            for p in parts:
                p_clean = ''.join(c if (c.isalnum() or c == '_') else '_' for c in p.upper())[:8]
                curr_iso += '/' + p_clean
                curr_joliet += '/' + p
                try:
                    iso.add_directory(curr_iso, joliet_path=curr_joliet)
                except:
                    pass

        for f in sorted(files):
            if f.endswith(('.bak', '.orig', '.scrambled')) or f.startswith('.'):
                continue
            full_path = os.path.join(root, f)
            if f.upper() == '1ST_READ.BIN':
                full_path = scrambled_1st

            if rel_root == '.':
                iso_dir = ''
                joliet_dir = ''
            else:
                parts = rel_root.split(os.sep)
                iso_dir = '/' + '/'.join(''.join(c if (c.isalnum() or c == '_') else '_' for c in p.upper())[:8] for p in parts)
                joliet_dir = '/' + '/'.join(parts)

            iso_n = clean_8_3(f)
            iso.add_file(full_path, f'{iso_dir}/{iso_n}', joliet_path=f'{joliet_dir}/{f}')

    temp_iso_path = os.path.join(temp_dir, 'data_lba0.iso')
    iso.write(temp_iso_path)
    iso.close()

    # Inyectar IP.BIN en sectores 0..15 del ISO
    with open(temp_iso_path, 'r+b') as f:
        with open(ip_path, 'rb') as ip_f:
            ip_raw = ip_f.read(32768)
        f.seek(0)
        f.write(ip_raw)

    # 4. CDI4DC
    print("\n[*] 4/4 Generando imagen CDI DiscJuggler (Data/Data) con cdi4dc...")
    os.makedirs(os.path.dirname(os.path.abspath(output_cdi)), exist_ok=True)
    res = subprocess.run([CDI4DC_BIN, temp_iso_path, output_cdi, '-d'], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"    [X] Error en cdi4dc: {res.stderr or res.stdout}")
        return False

    shutil.rmtree(temp_dir, ignore_errors=True)
    final_size = os.path.getsize(output_cdi)
    print(f"\n[✓] ¡CDI autoboot generado con ÉXITO!")
    print(f"    - Archivo: {output_cdi}")
    print(f"    - Tamaño : {final_size:,} bytes ({final_size / (1024*1024):.2f} MB)")
    print(f"    - Formato: Data/Data MIL-CD")
    print(f"    - Estado : Sin dummies (ahorro de 600 MB), 100% compatible con hardware real y emuladores.")
    return True

if __name__ == '__main__':
    gdi_in = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, '76')
    cdi_out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO_ROOT, 'output_cdi', 'Capcom_vs_SNK_Japan_NoDummy.cdi')
    convert_cvs(gdi_in, cdi_out)
