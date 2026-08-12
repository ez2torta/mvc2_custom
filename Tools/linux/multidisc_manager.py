#!/usr/bin/env python3
"""
multidisc_manager.py - Gestor y Constructor de Discos Multijuego y Multi-Soundtrack para Sega Dreamcast.

Permite:
1. Extraer juegos y bandas sonoras de compilaciones multijuego (como TDCFinal2.cdi) preservando hardlinks reales.
2. Construir compilaciones personalizadas de MvC2, CvS2, Super Turbo y 3rd Strike con múltiples
   soundtracks usando de-duplicación por bloques en ISO9660 puro en Python (Shared Sector Extents).
3. Generar la imagen CDI autoboot final de 2 sesiones (LBA 11702 o LBA 45000) 100% compatible con hardware real.
"""

import os
import sys
import time
import struct
import shutil
import argparse
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CDI4DC_BIN = os.path.join(SCRIPT_DIR, 'cdi4dc')

def encode_both_16(val):
    return struct.pack('<H', val) + struct.pack('>H', val)

def encode_both_32(val):
    return struct.pack('<I', val) + struct.pack('>I', val)

def make_dir_record(lba, size, flags, name_bytes):
    name_len = len(name_bytes)
    rec_len = 33 + name_len
    if rec_len % 2 != 0:
        rec_len += 1 # Align to even byte length
    
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

def build_shared_extent_iso(source_tree_dir, output_iso_path, volume_name="MULTIDISC", ip_bin_path=None, verbose=True):
    """
    Genera un archivo ISO9660 Nivel 1/2 en Python puro con soporte completo para
    Shared Extents (múltiples rutas apuntando al mismo LBA de inicio para hardlinks).
    """
    print("========================================================================")
    print("    Generador ISO9660 con De-duplicación de Sectores (Shared Extents)")
    print("========================================================================")
    print(f"[*] Directorio Origen: {source_tree_dir}")
    print(f"[*] Nombre Volumen   : {volume_name}")
    print(f"[*] ISO Salida       : {output_iso_path}")

    # 1. Indexar directorios
    dirs = []
    dir_to_idx = {}
    
    for root, dirnames, filenames in os.walk(source_tree_dir):
        rel = os.path.relpath(root, source_tree_dir).replace('\\', '/')
        if rel == '.': rel = ''
        dir_to_idx[rel] = len(dirs) + 1
        dirs.append({
            'rel': rel,
            'name': os.path.basename(rel) if rel else '',
            'parent_idx': 1,
            'subdirs': sorted(dirnames),
            'files': sorted(filenames),
            'full_path': root
        })

    for d in dirs:
        if d['rel']:
            parent_rel = os.path.dirname(d['rel']).replace('\\', '/')
            d['parent_idx'] = dir_to_idx[parent_rel]

    print(f"[+] Total directorios: {len(dirs):,}")

    # 2. Planificar el layout de LBA
    # Sectores del sistema:
    # 0..15: System area (IP.BIN)
    # 16: PVD
    # 17: VDST (Volume Descriptor Set Terminator)
    # 18..19: Little/Big Endian Path Tables
    # 20..: Tablas de directorios
    pvd_lba = 16
    vdst_lba = 17
    l_path_table_lba = 18
    m_path_table_lba = 19
    
    dir_start_lba = 20
    current_dir_lba = dir_start_lba

    # 3. Asignar LBAs para directorios
    for d in dirs:
        d['lba'] = current_dir_lba
        # Calcular tamaño del directorio en bytes
        # . y ..
        entries_len = len(make_dir_record(0, 0, 2, b'\x00')) + len(make_dir_record(0, 0, 2, b'\x01'))
        for s in d['subdirs']:
            entries_len += len(make_dir_record(0, 0, 2, s.upper().encode('ascii')))
        for f in d['files']:
            fn = f.upper()
            if ';' not in fn: fn += ';1'
            entries_len += len(make_dir_record(0, 0, 0, fn.encode('ascii', errors='ignore')))
        
        sectors_needed = max(1, (entries_len + 2047) // 2048)
        d['size'] = sectors_needed * 2048
        current_dir_lba += sectors_needed

    data_start_lba = current_dir_lba

    # 4. Asignar LBAs para archivos (con de-duplicación por inodo / hardlink)
    inode_to_lba = {}
    unique_file_tasks = [] # (full_path, lba, size)
    unique_count = 0
    shared_count = 0
    saved_bytes = 0

    current_data_lba = data_start_lba

    for d in dirs:
        d['file_records'] = []
        for f in d['files']:
            full_p = os.path.join(d['full_path'], f)
            st = os.stat(full_p)
            size = st.st_size
            key = (st.st_dev, st.st_ino)

            if key in inode_to_lba:
                file_lba = inode_to_lba[key]
                shared_count += 1
                saved_bytes += size
            else:
                file_lba = current_data_lba
                inode_to_lba[key] = file_lba
                sec_count = (size + 2047) // 2048
                current_data_lba += max(1, sec_count)
                unique_file_tasks.append((full_p, file_lba, size))
                unique_count += 1

            d['file_records'].append((f, file_lba, size))

    total_sectors = current_data_lba
    print(f"[+] Archivos únicos a escribir : {unique_count:,}")
    print(f"[+] Archivos enlazados (Hardlinks): {shared_count:,} (Ahorro: {saved_bytes / (1024*1024):.2f} MB!)")
    print(f"[+] Espacio final de la ISO    : {total_sectors * 2048:,} bytes ({total_sectors * 2048 / (1024*1024):.2f} MB)")

    # 5. Escribir archivo ISO
    with open(output_iso_path, 'wb') as iso_f:
        # 5.1 System Area (Sectores 0..15 - IP.BIN)
        ip_data = bytearray(16 * 2048)
        if ip_bin_path and os.path.exists(ip_bin_path):
            with open(ip_bin_path, 'rb') as ip_f:
                raw_ip = ip_f.read(32768)
                ip_data[:len(raw_ip)] = raw_ip
        iso_f.write(ip_data)

        # 5.2 PVD (Sector 16)
        pvd = bytearray(2048)
        pvd[0] = 1 # Type 1
        pvd[1:6] = b'CD001'
        pvd[6] = 1 # Version 1
        pvd[8:40] = b'SEGA SEGAKATANA                 ' # System ID
        pvd[40:72] = volume_name.upper().ljust(32).encode('ascii')[:32] # Volume ID
        pvd[80:88] = encode_both_32(total_sectors)
        pvd[120:124] = encode_both_16(1) # Volume Set Size
        pvd[124:128] = encode_both_16(1) # Volume Sequence Number
        pvd[128:132] = encode_both_16(2048) # Logical Block Size
        pvd[132:140] = encode_both_32(2048) # Path Table Size
        pvd[140:144] = struct.pack('<I', l_path_table_lba) # L Path Table
        pvd[148:152] = struct.pack('>I', m_path_table_lba) # M Path Table
        # Root directory record in PVD
        root_dir_rec = make_dir_record(dirs[0]['lba'], dirs[0]['size'], 2, b'\x00')
        pvd[156:156+len(root_dir_rec)] = root_dir_rec
        pvd[190:318] = volume_name.upper().ljust(128).encode('ascii')[:128]
        iso_f.write(pvd)

        # 5.3 VDST (Sector 17)
        vdst = bytearray(2048)
        vdst[0] = 255 # Terminator
        vdst[1:6] = b'CD001'
        vdst[6] = 1
        iso_f.write(vdst)

        # 5.4 Path Tables (Sectores 18 y 19)
        l_pt = bytearray()
        for idx, d in enumerate(dirs):
            d_name = d['name'].upper().encode('ascii') if d['name'] else b'\x00'
            rec = bytearray()
            rec.append(len(d_name))
            rec.append(0) # Ext attribute length
            rec.extend(struct.pack('<I', d['lba']))
            rec.extend(struct.pack('<H', d['parent_idx']))
            rec.extend(d_name)
            if len(rec) % 2 != 0: rec.append(0)
            l_pt.extend(rec)
        
        l_pt_padded = bytearray(2048)
        l_pt_padded[:len(l_pt)] = l_pt[:2048]
        iso_f.write(l_pt_padded)

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

        m_pt_padded = bytearray(2048)
        m_pt_padded[:len(m_pt)] = m_pt[:2048]
        iso_f.write(m_pt_padded)

        # 5.5 Escribir Tablas de Directorios (Sectores 20..)
        for d in dirs:
            dir_bytes = bytearray()
            # .
            dir_bytes.extend(make_dir_record(d['lba'], d['size'], 2, b'\x00'))
            # ..
            parent_d = dirs[d['parent_idx'] - 1]
            dir_bytes.extend(make_dir_record(parent_d['lba'], parent_d['size'], 2, b'\x01'))
            # Subdirs
            for s_name in d['subdirs']:
                sub_rel = f"{d['rel']}/{s_name}".lstrip('/')
                sub_d = dirs[dir_to_idx[sub_rel] - 1]
                dir_bytes.extend(make_dir_record(sub_d['lba'], sub_d['size'], 2, s_name.upper().encode('ascii')))
            # Files
            for f_name, f_lba, f_size in d['file_records']:
                fn = f_name.upper()
                if ';' not in fn: fn += ';1'
                dir_bytes.extend(make_dir_record(f_lba, f_size, 0, fn.encode('ascii', errors='ignore')))

            # Pad directory to allocated sectors
            pad_len = d['size'] - len(dir_bytes)
            if pad_len > 0:
                dir_bytes.extend(b'\x00' * pad_len)
            iso_f.write(dir_bytes[:d['size']])

        # 5.6 Escribir Datos de Archivos Únicos (Sectores data_start_lba..)
        print("[*] Escribiendo contenido físico de archivos a la ISO...")
        for idx, (f_path, f_lba, f_size) in enumerate(unique_file_tasks):
            with open(f_path, 'rb') as in_f:
                while chunk := in_f.read(1024 * 1024):
                    iso_f.write(chunk)
            # Pad file to 2048-byte sector boundary
            rem = f_size % 2048
            if rem != 0:
                iso_f.write(b'\x00' * (2048 - rem))

            if verbose and (idx + 1) % 500 == 0:
                print(f"    [{idx+1:4}/{len(unique_file_tasks)}] Archivos físicos escritos...")

    print(f"\n[✓] ¡ISO generada con ÉXITO!")
    print(f"    - Archivo: {output_iso_path}")
    print(f"    - Tamaño : {os.path.getsize(output_iso_path):,} bytes ({os.path.getsize(output_iso_path) / (1024*1024):.2f} MB)")
    return True

def extract_cdi_track2(cdi_path, output_dir, verbose=True):
    if not os.path.exists(cdi_path):
        print(f"[-] Error: Archivo CDI no encontrado: {cdi_path}")
        return False

    os.makedirs(output_dir, exist_ok=True)
    
    print("========================================================================")
    print("       Extractor de Discos Multijuego / Multi-Soundtrack (Dreamcast)")
    print("========================================================================")
    print(f"[*] CDI Origen : {cdi_path} ({os.path.getsize(cdi_path):,} bytes)")
    print(f"[*] Destino    : {output_dir}")

    with open(cdi_path, 'rb') as f:
        pos = 0
        track2_offset = None
        base_lba = 45000
        
        f.seek(79000000)
        chunk = f.read(1000000)
        sig_pos = chunk.find(b'SEGA SEGAKATANA')
        if sig_pos != -1:
            track2_offset = 79000000 + sig_pos
            print(f"[+] Pista de datos Track 2 encontrada en offset 0x{track2_offset:X} ({track2_offset:,} bytes)")
        else:
            track2_offset = 350408
            base_lba = 0
            print(f"[*] Usando offset Data/Data estándar: {track2_offset}")

        def read_iso_bytes(lba, length):
            if length == 0: return b''
            if lba < base_lba:
                f.seek(8 + lba * 2352)
                num_sectors = (length + 2047) // 2048
                buf = bytearray()
                for _ in range(num_sectors):
                    sec = f.read(2352)
                    if len(sec) < 2352: break
                    buf.extend(sec[:2048])
                return bytes(buf[:length])
            else:
                rel_sector = lba - base_lba
                f.seek(track2_offset + rel_sector * 2336)
                num_sectors = (length + 2047) // 2048
                buf = bytearray()
                for _ in range(num_sectors):
                    sec = f.read(2336)
                    if len(sec) < 2336: break
                    buf.extend(sec[:2048])
                return bytes(buf[:length])

        pvd_data = read_iso_bytes(base_lba + 16, 2048)
        vol_id = pvd_data[40:72].decode('latin1', errors='replace').strip()
        print(f"[+] Volumen ISO: '{vol_id}' (Base LBA: {base_lba})")

        root_rec = pvd_data[156:190]
        root_lba = struct.unpack('<I', root_rec[2:6])[0]
        root_len = struct.unpack('<I', root_rec[10:14])[0]

        def parse_dir(lba, length, current_path='/'):
            dir_data = read_iso_bytes(lba, length)
            pos = 0
            entries = []
            while pos < len(dir_data):
                rec_len = dir_data[pos]
                if rec_len == 0:
                    pos = ((pos // 2048) + 1) * 2048
                    continue
                rec = dir_data[pos:pos+rec_len]
                if len(rec) < 33:
                    pos += rec_len
                    continue
                ext_lba = struct.unpack('<I', rec[2:6])[0]
                data_len = struct.unpack('<I', rec[10:14])[0]
                flags = rec[25]
                name_len = rec[32]
                name = rec[33:33+name_len].decode('latin1', errors='replace').split(';1')[0]
                is_dir = bool(flags & 2)
                if name not in ('\x00', '\x01', ''):
                    entries.append({
                        'name': name,
                        'path': f'{current_path}/{name}'.replace('//', '/'),
                        'lba': ext_lba,
                        'size': data_len,
                        'is_dir': is_dir
                    })
                pos += rec_len
            return entries

        all_files = []
        all_dirs = []

        def walk(lba, length, path):
            sub_entries = parse_dir(lba, length, path)
            for e in sub_entries:
                if e['is_dir']:
                    all_dirs.append(e)
                    walk(e['lba'], e['size'], e['path'])
                else:
                    all_files.append(e)

        print("[*] Leyendo árbol de directorios de la imagen...")
        walk(root_lba, root_len, '')
        print(f"[+] Total directorios: {len(all_dirs)}, Total archivos: {len(all_files)}")

        for d in all_dirs:
            dir_path = os.path.join(output_dir, d['path'].lstrip('/'))
            os.makedirs(dir_path, exist_ok=True)

        lba_to_created_path = {}
        extracted_bytes = 0
        saved_bytes = 0

        print("[*] Extrayendo archivos y vinculando hardlinks...")
        for idx, f_item in enumerate(all_files):
            file_lba = f_item['lba']
            file_size = f_item['size']
            target_path = os.path.join(output_dir, f_item['path'].lstrip('/'))
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            if file_lba in lba_to_created_path and os.path.exists(lba_to_created_path[file_lba]):
                src_link = lba_to_created_path[file_lba]
                try:
                    if os.path.exists(target_path): os.remove(target_path)
                    os.link(src_link, target_path)
                    saved_bytes += file_size
                except Exception:
                    data = read_iso_bytes(file_lba, file_size)
                    with open(target_path, 'wb') as out_f:
                        out_f.write(data)
            else:
                data = read_iso_bytes(file_lba, file_size)
                with open(target_path, 'wb') as out_f:
                    out_f.write(data)
                lba_to_created_path[file_lba] = target_path
                extracted_bytes += file_size

            if verbose and (idx + 1) % 500 == 0:
                print(f"    [{idx+1:4}/{len(all_files)}] Procesados...")

    print("\n[✓] ¡Extracción completada con ÉXITO!")
    print(f"    - Archivos extraídos: {len(all_files):,}")
    print(f"    - Espacio Físico Real: {extracted_bytes:,} bytes ({extracted_bytes/(1024*1024):.2f} MB)")
    print(f"    - Espacio Ahorrado por Hardlinks: {saved_bytes:,} bytes ({saved_bytes/(1024*1024):.2f} MB!)")
    return True

def build_multidisc_cdi(source_tree_dir, output_cdi_path, volume_name="MULTIDISC", verbose=True):
    if not os.path.exists(source_tree_dir):
        print(f"[-] Error: Directorio de origen no encontrado: {source_tree_dir}")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_cdi_path)), exist_ok=True)
    temp_iso = os.path.join(os.path.dirname(output_cdi_path), '_temp_multidisc.iso')

    ip_bin_path = os.path.join(source_tree_dir, 'IP.BIN')
    if not os.path.exists(ip_bin_path):
        ip_bin_path = os.path.join(ROOT_DIR, 'MVC2', 'IP.BIN')

    # 1. Construir ISO con de-duplicación nativa en Python
    build_shared_extent_iso(source_tree_dir, temp_iso, volume_name=volume_name, ip_bin_path=ip_bin_path, verbose=verbose)

    # 2. Convertir a CDI con cdi4dc
    print("\n[*] Generando contenedor CDI DiscJuggler (Data/Data) con cdi4dc...")
    if os.path.exists(output_cdi_path):
        os.remove(output_cdi_path)

    cmd_cdi = [CDI4DC_BIN, temp_iso, output_cdi_path, '-d']
    res_cdi = subprocess.run(cmd_cdi, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    if os.path.exists(temp_iso):
        os.remove(temp_iso)

    if not os.path.exists(output_cdi_path):
        print(f"[-] Error en cdi4dc:\n{res_cdi.stdout}")
        return False

    cdi_size = os.path.getsize(output_cdi_path)
    print(f"\n[✓] ¡Imagen CDI Multijuego generada con ÉXITO!")
    print(f"    - Archivo: {output_cdi_path}")
    print(f"    - Tamaño : {cdi_size:,} bytes ({cdi_size / (1024*1024):.2f} MB)")
    return True

def build_from_modules(output_cdi_path, volume_name="CAPCOM_FIGHT_PACK", games_dir=None, mvc2_nene_dir=None, verbose=True):
    """
    Ensambla y compila directamente el Capcom Fight Pack a partir de las carpetas modulares en Games/ y MVC2/.
    No requiere extracción previa ni duplica archivos en disco.
    """
    if games_dir is None:
        games_dir = os.path.join(ROOT_DIR, "Games")
    if mvc2_nene_dir is None:
        mvc2_nene_dir = os.path.join(ROOT_DIR, "MVC2")

    staging_dir = os.path.join(os.path.dirname(os.path.abspath(output_cdi_path)), "_staging_multidisc")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    print("========================================================================")
    print("   Ensamblador Modular de Compilaciones Dreamcast (Capcom Fight Pack)")
    print("========================================================================")
    print(f"[*] Directorio de Módulos: {games_dir}")
    print(f"[*] MvC2 Nene Edition    : {mvc2_nene_dir}")
    print(f"[*] CDI Destino          : {output_cdi_path}")

    # 1. Base Frontend (DreamKey / XDP HTML, Fonts, Saves, Launchers)
    fe_src = os.path.join(games_dir, "Frontend")
    for item in os.listdir(fe_src):
        s = os.path.join(fe_src, item)
        d = os.path.join(staging_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, copy_function=os.link)
        elif os.path.isfile(s):
            os.link(s, d)

    # 2. Bóveda Central de Audio ADX
    adx_src = os.path.join(games_dir, "Soundtracks", "ADXFILES")
    if os.path.exists(adx_src):
        shutil.copytree(adx_src, os.path.join(staging_dir, "ADXFILES"), copy_function=os.link)

    mapping_src = os.path.join(games_dir, "Soundtracks", "MAPPING")
    if os.path.exists(mapping_src):
        shutil.copytree(mapping_src, os.path.join(staging_dir, "MAPPING"), copy_function=os.link)

    # 3. MvC2 Vanilla (USAMVC + variantes)
    vanilla_src = os.path.join(games_dir, "MVC2_Vanilla")
    for v in ["USAMVC", "GAME20", "GAME24", "GAME27", "GAME28"]:
        dst_v = os.path.join(staging_dir, v)
        shutil.copytree(vanilla_src, dst_v, copy_function=os.link)

    # 4. MvC2 Nene Edition (MVC2NENE + variantes)
    for g_name in ["MVC2NENE", "GAMENENE0", "GAMENENE1", "GAMENENE2", "GAMENENE3", "GAMENENE4", "GAMENENE5", "GAMENENE6"]:
        dst_n = os.path.join(staging_dir, g_name)
        os.makedirs(dst_n, exist_ok=True)
        for root, dirs, files in os.walk(mvc2_nene_dir):
            rel = os.path.relpath(root, mvc2_nene_dir)
            target_d = os.path.join(dst_n, rel)
            os.makedirs(target_d, exist_ok=True)
            for f in files:
                if f.endswith(('.bak', '.orig', '.backup.BIN')) or f.startswith('.'): continue
                src_f = os.path.join(root, f)
                dst_f = os.path.join(target_d, f)
                ref_f = os.path.join(vanilla_src, rel, f) if rel != '.' else os.path.join(vanilla_src, f)
                if os.path.exists(ref_f) and os.path.getsize(ref_f) == os.path.getsize(src_f):
                    try:
                        os.link(ref_f, dst_f)
                        continue
                    except: pass
                if f.startswith("ADX_") and os.path.exists(os.path.join(vanilla_src, f)):
                    os.link(os.path.join(vanilla_src, f), dst_f)
                    continue
                else:
                    try:
                        os.link(src_f, dst_f)
                    except:
                        shutil.copy2(src_f, dst_f)

    # 5. CvS2 (JAPCVS + variantes)
    cvs_src = os.path.join(games_dir, "CVS2")
    for v in ["JAPCVS", "GAME60", "GAME62", "GAME64", "GAME67"]:
        dst_v = os.path.join(staging_dir, v)
        shutil.copytree(cvs_src, dst_v, copy_function=os.link)

    # 6. SSF2X (TST + variantes)
    st_src = os.path.join(games_dir, "SSF2X")
    for v in ["TST", "GAME90", "GAME92", "GAME94", "GAME96"]:
        dst_v = os.path.join(staging_dir, v)
        shutil.copytree(st_src, dst_v, copy_function=os.link)

    # 7. SPF2X (TPF + variantes)
    pf_src = os.path.join(games_dir, "SPF2X")
    for v in ["TPF", "GAME100", "GAME102", "GAME104"]:
        dst_v = os.path.join(staging_dir, v)
        shutil.copytree(pf_src, dst_v, copy_function=os.link)

    print("[+] Staging completado con hardlinks (0 MB adicionales).")

    # Build ISO and CDI
    build_multidisc_cdi(staging_dir, output_cdi_path, volume_name=volume_name, verbose=verbose)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return True

def main():
    parser = argparse.ArgumentParser(description='Gestor de compilaciones Multijuego y Multi-Soundtrack para Dreamcast')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')

    p_extract = subparsers.add_parser('extract', help='Extrae un CDI multijuego preservando hardlinks')
    p_extract.add_argument('--input', '-i', required=True, help='Ruta al archivo .cdi origen (ej: TDCFinal2/disc.cdi)')
    p_extract.add_argument('--output', '-o', required=True, help='Directorio de salida para los juegos extraídos')

    p_build = subparsers.add_parser('build', help='Construye un CDI multijuego/multi-soundtrack con de-duplicación')
    p_build.add_argument('--input', '-i', required=True, help='Directorio con la estructura de juegos y hardlinks')
    p_build.add_argument('--output', '-o', required=True, help='Ruta del archivo .cdi de salida')
    p_build.add_argument('--volume', '-v', default='MULTIDISC', help='Nombre de volumen ISO')

    p_modular = subparsers.add_parser('build-modular', help='Ensambla y compila directamente desde Games/ y MVC2/')
    p_modular.add_argument('--output', '-o', required=True, help='Ruta del archivo .cdi de salida')
    p_modular.add_argument('--games-dir', default=None, help='Directorio con módulos Games/')
    p_modular.add_argument('--nene-dir', default=None, help='Directorio con MvC2 Nene Edition')
    p_modular.add_argument('--volume', '-v', default='CAPCOM_FIGHT_PACK', help='Nombre de volumen ISO')

    args = parser.parse_args()

    if args.command == 'extract':
        extract_cdi_track2(args.input, args.output)
    elif args.command == 'build':
        build_multidisc_cdi(args.input, args.output, volume_name=args.volume)
    elif args.command == 'build-modular':
        build_from_modules(args.output, volume_name=args.volume, games_dir=args.games_dir, mvc2_nene_dir=args.nene_dir)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
