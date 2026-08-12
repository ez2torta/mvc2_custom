#!/usr/bin/env python3
"""
extractor.py - Extractor quirúrgico de pistas de datos CDI con preservación de hardlinks.
"""

import os
import struct

def extract_cdi_track2(cdi_path: str, output_dir: str, verbose: bool = True):
    """
    Extrae quirúrgicamente todos los archivos y directorios de la pista de datos (Pista 2)
    de un contenedor CDI DiscJuggler, detectando y preservando hardlinks.
    """
    if verbose:
        print(f"[*] Extrayendo pista de datos desde: {cdi_path}")
        print(f"[*] Destino: {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    with open(cdi_path, 'rb') as f:
        # Detectar cabecera SEGA SEGAKATANA en LBA 45000 (offset estándar 79,190,408 bytes)
        track2_offset = 79190408
        f.seek(track2_offset)
        magic = f.read(16)
        if magic != b'SEGA SEGAKATANA ':
            # Buscar dinámicamente si no está en el offset estándar
            f.seek(0)
            chunk_sz = 10 * 1024 * 1024
            offset = 0
            found = False
            while offset < os.path.getsize(cdi_path):
                chunk = f.read(chunk_sz)
                idx = chunk.find(b'SEGA SEGAKATANA ')
                if idx != -1:
                    track2_offset = offset + idx
                    found = True
                    break
                offset += len(chunk)
            if not found:
                raise ValueError("No se encontró la cabecera SEGA Katana en el CDI especificado.")

        base_lba = 45000
        sec_size = 2336

        def read_sec_data(lba, num_sec=1):
            f.seek(track2_offset + (lba - base_lba) * sec_size)
            buf = bytearray()
            for _ in range(num_sec):
                buf.extend(f.read(sec_size)[:2048])
            return bytes(buf)

        # Leer PVD en Sector 16
        pvd_data = read_sec_data(base_lba + 16, 1)
        root_rec = pvd_data[156:156+34]
        root_lba = int.from_bytes(root_rec[2:6], 'little')
        root_sz = int.from_bytes(root_rec[10:14], 'little')

        extracted_lbas = {} # lba -> ruta_primer_archivo

        def extract_directory(d_lba, d_sz, cur_dst):
            os.makedirs(cur_dst, exist_ok=True)
            d_data = read_sec_data(d_lba, (d_sz + 2047) // 2048)[:d_sz]
            pos = 0
            while pos < len(d_data):
                rlen = d_data[pos]
                if rlen == 0:
                    pos = ((pos // 2048) + 1) * 2048
                    continue
                rec = d_data[pos:pos+rlen]
                if len(rec) < 33: break
                f_ext = int.from_bytes(rec[2:6], 'little')
                f_size = int.from_bytes(rec[10:14], 'little')
                flags = rec[25]
                nlen = rec[32]
                fname = rec[33:33+nlen].decode('latin1', errors='replace').split(';')[0]

                if fname not in ('\x00', '\x01'):
                    target_path = os.path.join(cur_dst, fname)
                    if flags & 2:
                        extract_directory(f_ext, f_size, target_path)
                    else:
                        if f_size == 0:
                            open(target_path, 'wb').close()
                        elif f_ext in extracted_lbas:
                            # Reutilizar hardlink existente
                            os.link(extracted_lbas[f_ext], target_path)
                        else:
                            content = read_sec_data(f_ext, (f_size + 2047) // 2048)[:f_size]
                            with open(target_path, 'wb') as out_f:
                                out_f.write(content)
                            extracted_lbas[f_ext] = target_path
                pos += rlen

        extract_directory(root_lba, root_sz, output_dir)

    if verbose:
        print(f"[✓] Extracción completada exitosamente en: {output_dir}")
    return True

def extract_gdi(gdi_path_or_dir: str, output_dir: str, verbose: bool = True):
    """
    Extrae todos los archivos de un volcado nativo GD-ROM (GDI de Dreamcast):
    - Parsea disc.gdi para localizar la pista de alta densidad (Pista 3 a LBA 45000).
    - Autodetecta el formato de sector (Mode 1 2352 bytes con sync, 2048 bytes raw, o Mode 2).
    - Extrae el árbol completo ISO9660 con sus archivos limpios y sin hacks de CD-R.
    """
    # 1. Localizar archivo .gdi
    if os.path.isdir(gdi_path_or_dir):
        gdi_files = [f for f in os.listdir(gdi_path_or_dir) if f.lower().endswith('.gdi')]
        if not gdi_files:
            raise FileNotFoundError(f"No se encontró ningún archivo .gdi en el directorio: {gdi_path_or_dir}")
        gdi_file = os.path.join(gdi_path_or_dir, gdi_files[0])
        gdi_base_dir = gdi_path_or_dir
    else:
        gdi_file = gdi_path_or_dir
        gdi_base_dir = os.path.dirname(os.path.abspath(gdi_file))

    if verbose:
        print(f"[*] Leyendo descriptor GDI: {gdi_file}")

    # 2. Parsear disc.gdi
    with open(gdi_file, 'r', encoding='latin1') as gf:
        lines = [line.strip() for line in gf if line.strip()]

    if len(lines) < 2:
        raise ValueError(f"Formato de archivo GDI inválido: {gdi_file}")

    num_tracks = int(lines[0])
    track3_info = None

    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 5:
            track_num = int(parts[0])
            track_lba = int(parts[1])
            track_type = int(parts[2])
            track_sec_sz = int(parts[3])
            track_filename = parts[4]
            # La pista de datos principal de Dreamcast es la pista de alta densidad a LBA >= 45000
            if track_lba >= 45000:
                track3_info = (track_num, track_lba, track_sec_sz, track_filename)
                break

    if not track3_info:
        # Si no se encontró por LBA 45000, tomar la última pista de datos (típicamente track03.bin)
        parts = lines[-1].split()
        track3_info = (int(parts[0]), int(parts[1]), int(parts[3]), parts[4])

    t_num, base_lba, sec_size, track_rel_path = track3_info
    track_bin_path = os.path.join(gdi_base_dir, track_rel_path)

    if not os.path.exists(track_bin_path):
        raise FileNotFoundError(f"No se encontró el archivo de pista de datos: {track_bin_path}")

    if verbose:
        print(f"[*] Pista de datos identificada: {track_rel_path} (LBA: {base_lba}, Sector: {sec_size}B)")
        print(f"[*] Extrayendo archivos a: {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    with open(track_bin_path, 'rb') as tf:
        # Detectar offset del payload dentro del sector (Mode 1 2352 tiene 16 bytes de sync)
        payload_offset = 0
        if sec_size == 2352:
            sec0 = tf.read(2352)
            # Sync header Mode 1: 00 ff ff ff ff ff ff ff ff ff ff 00
            if sec0.startswith(b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'):
                payload_offset = 16
        elif sec_size == 2336:
            payload_offset = 8 # Mode 2 Form 1 subheader

        def read_gdi_sec_data(lba, num_sec=1):
            buf = bytearray()
            for i in range(num_sec):
                tf.seek((lba + i - base_lba) * sec_size + payload_offset)
                buf.extend(tf.read(2048))
            return bytes(buf)

        # Leer PVD en Sector 16
        pvd_data = read_gdi_sec_data(base_lba + 16, 1)
        if pvd_data[1:6] != b'CD001':
            raise ValueError(f"Identificador ISO9660 no encontrado en sector 16 de {track_rel_path}")

        vol_id = pvd_data[40:72].decode('latin1', errors='replace').strip()
        root_rec = pvd_data[156:156+34]
        root_lba = int.from_bytes(root_rec[2:6], 'little')
        root_sz = int.from_bytes(root_rec[10:14], 'little')

        if verbose:
            print(f"    - Volumen ISO: {vol_id}")
            print(f"    - Root Dir LBA: {root_lba} ({root_sz:,} bytes)")

        extracted_count = 0

        def extract_gdi_directory(d_lba, d_sz, cur_dst):
            nonlocal extracted_count
            os.makedirs(cur_dst, exist_ok=True)
            d_data = read_gdi_sec_data(d_lba, (d_sz + 2047) // 2048)[:d_sz]
            pos = 0
            while pos < len(d_data):
                rlen = d_data[pos]
                if rlen == 0:
                    pos = ((pos // 2048) + 1) * 2048
                    continue
                rec = d_data[pos:pos+rlen]
                if len(rec) < 33: break
                f_ext = int.from_bytes(rec[2:6], 'little')
                f_size = int.from_bytes(rec[10:14], 'little')
                flags = rec[25]
                nlen = rec[32]
                fname = rec[33:33+nlen].decode('latin1', errors='replace').split(';')[0]

                if fname not in ('\x00', '\x01'):
                    target_path = os.path.join(cur_dst, fname)
                    if flags & 2:
                        extract_gdi_directory(f_ext, f_size, target_path)
                    else:
                        if f_size == 0:
                            open(target_path, 'wb').close()
                        else:
                            content = read_gdi_sec_data(f_ext, (f_size + 2047) // 2048)[:f_size]
                            with open(target_path, 'wb') as out_f:
                                out_f.write(content)
                        extracted_count += 1
                pos += rlen

        extract_gdi_directory(root_lba, root_sz, output_dir)

    if verbose:
        print(f"[✓] Extracción de GDI completada: {extracted_count:,} archivos extraídos en: {output_dir}")
    return True
