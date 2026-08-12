#!/usr/bin/env python3
"""
iso9660.py - Generador canónico de sistemas de archivos ISO9660 con BFS, Shared Extents y de-duplicación para Dreamcast.
"""

import os
import struct

def encode_both_16(val: int) -> bytes:
    """Codifica un entero de 16 bits en formato Both-Endian (Little-Endian + Big-Endian)."""
    return struct.pack('<H', val) + struct.pack('>H', val)

def encode_both_32(val: int) -> bytes:
    """Codifica un entero de 32 bits en formato Both-Endian (Little-Endian + Big-Endian)."""
    return struct.pack('<I', val) + struct.pack('>I', val)

def make_dir_record(lba: int, size: int, flags: int, name_bytes: bytes) -> bytes:
    """
    Construye un registro de directorio estándar ISO9660 con formato de fecha,
    Both-Endian LBA/Size y alineación a byte par.
    """
    name_len = len(name_bytes)
    rec_len = 33 + name_len
    if rec_len % 2 != 0:
        rec_len += 1 # Alinear a longitud de byte par

    buf = bytearray(rec_len)
    buf[0] = rec_len
    buf[1] = 0 # Extended Attribute length
    buf[2:10] = encode_both_32(lba)
    buf[10:18] = encode_both_32(size)

    # 7-byte date (year - 1900, month, day, hour, min, sec, offset)
    buf[18] = 126 # Year 2026
    buf[19] = 8   # Month
    buf[20] = 11  # Day
    buf[21] = 12  # Hour
    buf[22] = 0   # Min
    buf[23] = 0   # Sec
    buf[24] = 0   # Timezone offset

    buf[25] = flags
    buf[26] = 0 # File unit size
    buf[27] = 0 # Interleave gap
    buf[28:32] = encode_both_16(1) # Volume sequence number
    buf[32] = name_len
    buf[33:33+name_len] = name_bytes
    return bytes(buf)

def build_iso9660_with_deduplication(source_tree_dir: str, output_iso_path: str, volume_name: str = "MULTIDISC", ip_bin_path: str = None, base_lba: int = 45000, verbose: bool = True):
    """
    Genera un archivo ISO9660 Nivel 1 canónico en Python puro con soporte completo para
    Shared Extents (múltiples rutas apuntando al mismo LBA de inicio para hardlinks)
    masterizado a base_lba (45000 para compilaciones multijuego Audio/Data).
    """
    if verbose:
        print("========================================================================")
        print(f"    Generador ISO9660 con De-duplicación de Sectores (Base LBA: {base_lba})")
        print("========================================================================")
        print(f"[*] Directorio Origen: {source_tree_dir}")
        print(f"[*] Nombre Volumen   : {volume_name}")
        print(f"[*] ISO Salida       : {output_iso_path}")

    # Si no se pasó ip_bin_path explícito, buscarlo en la raíz de source_tree_dir
    if not ip_bin_path:
        candidate_ip = os.path.join(source_tree_dir, 'IP.BIN')
        if os.path.exists(candidate_ip):
            ip_bin_path = candidate_ip

    # 1. Indexar directorios en orden estricto de amplitud (Breadth-First Level-by-Level) conforme a la norma ISO9660
    raw_dirs = {}
    for root, dirnames, filenames in os.walk(source_tree_dir):
        rel = os.path.relpath(root, source_tree_dir).replace('\\', '/')
        if rel == '.': rel = ''
        raw_dirs[rel] = {
            'rel': rel,
            'name': os.path.basename(rel) if rel else '',
            'subdirs': sorted(dirnames),
            'files': sorted(filenames),
            'full_path': root
        }

    dirs = []
    dir_to_idx = {}
    queue = ['']

    while queue:
        curr_rel = queue.pop(0)
        curr_info = raw_dirs[curr_rel]
        dir_to_idx[curr_rel] = len(dirs) + 1

        sorted_subdirs = sorted(curr_info['subdirs'], key=lambda s: s.upper().encode('ascii'))
        for s in sorted_subdirs:
            sub_rel = f"{curr_rel}/{s}".lstrip('/')
            queue.append(sub_rel)

        dirs.append({
            'rel': curr_rel,
            'name': curr_info['name'],
            'parent_idx': 1,
            'subdirs': sorted_subdirs,
            'files': sorted(curr_info['files']),
            'full_path': curr_info['full_path']
        })

    for d in dirs:
        if d['rel']:
            parent_rel = os.path.dirname(d['rel']).replace('\\', '/')
            d['parent_idx'] = dir_to_idx[parent_rel]

    if verbose:
        print(f"[+] Total directorios indexados (BFS ISO9660): {len(dirs):,}")

    # 2. Construir plantilla de Path Table para calcular tamaño exacto en sectores
    l_pt_dummy = bytearray()
    for idx, d in enumerate(dirs):
        d_name = d['name'].upper().encode('ascii') if d['name'] else b'\x00'
        rec = bytearray()
        rec.append(len(d_name))
        rec.append(0)
        rec.extend(struct.pack('<I', 0))
        rec.extend(struct.pack('<H', d['parent_idx']))
        rec.extend(d_name)
        if len(rec) % 2 != 0: rec.append(0)
        l_pt_dummy.extend(rec)

    pt_size = len(l_pt_dummy)
    pt_sectors = max(1, (pt_size + 2047) // 2048)

    # 3. Layout canónico mkisofs / TDCFinal2:
    # Sector 0..15: System Area (IP.BIN)
    # Sector 16: PVD (LBA base_lba + 16)
    # Sector 17: VDST (LBA base_lba + 17)
    # Sector 18: Padding Zeros (LBA base_lba + 18)
    # Sector 19: L-Path Table (LBA base_lba + 19)
    # Sector 19 + pt_sectors: M-Path Table
    # Sector 19 + 2*pt_sectors: Tablas de Directorios (Root y Subdirectorios)
    pvd_lba = base_lba + 16
    vdst_lba = base_lba + 17
    l_path_table_lba = base_lba + 19
    m_path_table_lba = base_lba + 19 + pt_sectors
    dir_start_rel = 19 + 2 * pt_sectors
    current_dir_rel = dir_start_rel

    def append_dir_entry(dir_sectors_buf, entry_bytes):
        curr_offset = len(dir_sectors_buf) % 2048
        rem = 2048 - curr_offset
        if len(entry_bytes) > rem:
            dir_sectors_buf.extend(b'\x00' * rem)
        dir_sectors_buf.extend(entry_bytes)

    # 4. Asignar LBAs para directorios con alineación estricta a sectores de 2048 bytes
    for d in dirs:
        d['lba'] = base_lba + current_dir_rel
        dir_buf = bytearray()
        append_dir_entry(dir_buf, make_dir_record(0, 0, 2, b'\x00'))
        append_dir_entry(dir_buf, make_dir_record(0, 0, 2, b'\x01'))
        all_e = []
        for s in d['subdirs']:
            all_e.append((s.upper().encode('ascii'), 2))
        for f in d['files']:
            fn = f.upper()
            if ';' not in fn: fn += ';1'
            all_e.append((fn.encode('ascii', errors='ignore'), 0))
        all_e.sort(key=lambda x: x[0])
        for name_bytes, flags in all_e:
            append_dir_entry(dir_buf, make_dir_record(0, 0, flags, name_bytes))

        sectors_needed = max(1, (len(dir_buf) + 2047) // 2048)
        d['size'] = sectors_needed * 2048
        current_dir_rel += sectors_needed

    data_start_rel = current_dir_rel
    current_data_rel = data_start_rel

    # 5. Asignar LBAs para archivos (con de-duplicación por inodo / hardlink)
    inode_to_lba = {}
    unique_file_tasks = []
    unique_count = 0
    shared_count = 0
    saved_bytes = 0

    for d in dirs:
        d['file_records'] = []
        for f in d['files']:
            full_p = os.path.join(d['full_path'], f)
            st = os.stat(full_p)
            size = st.st_size
            key = (st.st_dev, st.st_ino)

            if size == 0:
                # Archivos de 0 bytes no consumen sectores físicos
                file_lba = base_lba + current_data_rel
                d['file_records'].append((f, file_lba, 0))
                continue

            if key in inode_to_lba:
                file_lba = inode_to_lba[key]
                shared_count += 1
                saved_bytes += size
            else:
                file_lba = base_lba + current_data_rel
                inode_to_lba[key] = file_lba
                sec_count = (size + 2047) // 2048
                current_data_rel += sec_count
                unique_file_tasks.append((full_p, file_lba, size))
                unique_count += 1

            d['file_records'].append((f, file_lba, size))

    total_iso_sectors = current_data_rel
    if verbose:
        print(f"[+] Root directory LBA = {dirs[0]['lba']} (Base LBA: {base_lba})")
        print(f"[+] Archivos únicos a escribir : {unique_count:,}")
        print(f"[+] Archivos enlazados (Hardlinks): {shared_count:,} (Ahorro: {saved_bytes / (1024*1024):.2f} MB!)")
        print(f"[+] Espacio final de la ISO    : {total_iso_sectors * 2048:,} bytes ({total_iso_sectors * 2048 / (1024*1024):.2f} MB)")

    # 6. Escribir archivo ISO
    os.makedirs(os.path.dirname(os.path.abspath(output_iso_path)), exist_ok=True)
    with open(output_iso_path, 'wb') as iso_f:
        # 6.1 System Area (Sectores 0..15: IP.BIN)
        ip_data = bytearray(32768)
        if ip_bin_path and os.path.exists(ip_bin_path):
            with open(ip_bin_path, 'rb') as ip_f:
                raw_ip = ip_f.read(32768)
                ip_data[:len(raw_ip)] = raw_ip
        iso_f.write(ip_data)

        # Construir Path Tables definitivas con los LBAs reales asignados
        l_pt = bytearray()
        for idx, d in enumerate(dirs):
            d_name = d['name'].upper().encode('ascii') if d['name'] else b'\x00'
            rec = bytearray()
            rec.append(len(d_name))
            rec.append(0)
            rec.extend(struct.pack('<I', d['lba']))
            rec.extend(struct.pack('<H', d['parent_idx']))
            rec.extend(d_name)
            if len(rec) % 2 != 0: rec.append(0)
            l_pt.extend(rec)

        m_pt = bytearray()
        for idx, d in enumerate(dirs):
            d_name = d['name'].upper().encode('ascii') if d['name'] else b'\x00'
            rec = bytearray()
            rec.append(len(d_name))
            rec.append(0)
            rec.extend(struct.pack('>I', d['lba']))
            rec.extend(struct.pack('>H', d['parent_idx']))
            rec.extend(d_name)
            if len(rec) % 2 != 0: rec.append(0)
            m_pt.extend(rec)

        # 6.2 PVD (Sector 16)
        pvd = bytearray(2048)
        pvd[0] = 1
        pvd[1:6] = b'CD001'
        pvd[6] = 1
        pvd[8:40] = b'LINUX                           '
        pvd[40:72] = volume_name.upper().ljust(32).encode('ascii')[:32]
        pvd[80:88] = encode_both_32(total_iso_sectors) # Volume Space Size
        pvd[120:124] = encode_both_16(1)
        pvd[124:128] = encode_both_16(1)
        pvd[128:132] = encode_both_16(2048)
        pvd[132:140] = encode_both_32(len(l_pt)) # Exact Path Table Size
        pvd[140:144] = struct.pack('<I', l_path_table_lba)
        pvd[148:152] = struct.pack('>I', m_path_table_lba)
        # Root directory record in PVD
        root_dir_rec = make_dir_record(dirs[0]['lba'], dirs[0]['size'], 2, b'\x00')
        pvd[156:156+len(root_dir_rec)] = root_dir_rec
        pvd[190:318] = b' ' * 128
        pvd[318:446] = b' ' * 128
        pvd[446:574] = b' ' * 128
        pvd[574:702] = b'MKISOFS ISO 9660/HFS FILESYSTEM BUILDER & CDRECORD CD-R/DVD CREATOR (C) 1993 E.YOUNGDALE (C) 1997 J.PEARSON/J.SCHILLING'.ljust(128)[:128]
        iso_f.write(pvd)

        # 6.3 VDST (Sector 17)
        vdst = bytearray(2048)
        vdst[0] = 255
        vdst[1:6] = b'CD001'
        vdst[6] = 1
        iso_f.write(vdst)

        # 6.3.1 Sector 18: Padding Zeros (Canónico mkisofs / TDCFinal2)
        iso_f.write(b'\x00' * 2048)

        # 6.4 Path Tables (Sectores 19..)
        l_pt_padded = bytearray(pt_sectors * 2048)
        l_pt_padded[:len(l_pt)] = l_pt
        iso_f.write(l_pt_padded)

        m_pt_padded = bytearray(pt_sectors * 2048)
        m_pt_padded[:len(m_pt)] = m_pt
        iso_f.write(m_pt_padded)

        # 6.5 Escribir Tablas de Directorios con ordenamiento ISO9660 estricto
        for d in dirs:
            iso_f.seek((d['lba'] - base_lba) * 2048)
            dir_bytes = bytearray()
            # . (Current dir)
            append_dir_entry(dir_bytes, make_dir_record(d['lba'], d['size'], 2, b'\x00'))
            # .. (Parent dir)
            parent_d = dirs[d['parent_idx'] - 1]
            append_dir_entry(dir_bytes, make_dir_record(parent_d['lba'], parent_d['size'], 2, b'\x01'))

            # Combinar subdirectorios y archivos en una sola lista y ordenar alfabéticamente por nombre ISO
            all_entries = []
            for s_name in d['subdirs']:
                sub_rel = f"{d['rel']}/{s_name}".lstrip('/')
                sub_d = dirs[dir_to_idx[sub_rel] - 1]
                iso_name = s_name.upper().encode('ascii')
                all_entries.append((iso_name, sub_d['lba'], sub_d['size'], 2))

            for f_name, f_lba, f_size in d['file_records']:
                fn = f_name.upper()
                if ';' not in fn: fn += ';1'
                iso_name = fn.encode('ascii', errors='ignore')
                all_entries.append((iso_name, f_lba, f_size, 0))

            # Ordenamiento estricto ISO9660 por los bytes del nombre
            all_entries.sort(key=lambda x: x[0])

            for iso_name, ext_lba, ext_size, flags in all_entries:
                append_dir_entry(dir_bytes, make_dir_record(ext_lba, ext_size, flags, iso_name))

            # Rellenar con ceros hasta el tamaño del sector
            pad_len = d['size'] - len(dir_bytes)
            if pad_len > 0:
                dir_bytes.extend(b'\x00' * pad_len)

            iso_f.write(dir_bytes[:d['size']])

        # 6.6 Escribir Datos de Archivos Únicos con seek exacto por LBA
        if verbose:
            print("[*] Escribiendo contenido físico de archivos a la ISO...")
        for idx, (f_path, f_lba, f_size) in enumerate(unique_file_tasks):
            if f_size == 0: continue
            iso_f.seek((f_lba - base_lba) * 2048)
            with open(f_path, 'rb') as in_f:
                while chunk := in_f.read(1024 * 1024):
                    iso_f.write(chunk)
            rem = f_size % 2048
            if rem != 0:
                iso_f.write(b'\x00' * (2048 - rem))

            if verbose and (idx + 1) % 500 == 0:
                print(f"    [{idx+1:4}/{len(unique_file_tasks)}] Archivos físicos escritos...")

    if verbose:
        print(f"\n[✓] ¡ISO generada con ÉXITO!")
        print(f"    - Archivo: {output_iso_path}")
        print(f"    - Tamaño : {os.path.getsize(output_iso_path):,} bytes ({os.path.getsize(output_iso_path) / (1024*1024):.2f} MB)")
    return True
