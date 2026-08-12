#!/usr/bin/env python3
"""
iso9660.py - Generador canónico de sistemas de archivos ISO9660 con BFS y de-duplicación de sectores para Dreamcast.
"""

import os
import struct
from collections import deque

def build_iso9660_with_deduplication(root_dir: str, output_iso_path: str, volume_name: str = "MULTIDISC", base_lba: int = 45000, verbose: bool = True):
    """
    Genera una imagen ISO9660 Nivel 1 canónica a LBA base (ej: 45000):
    - Recorrido Breadth-First Search (BFS) estricto para la tabla de rutas (Path Table).
    - Ordenamiento alfabético ASCII para directorios y archivos.
    - Soporte completo de Hardlinks (Inodos compartidos) para de-duplicación física de sectores.
    - Posicionamiento absoluto con seek para evitar desfases causados por archivos vacíos.
    """
    if verbose:
        print("========================================================================")
        print(f"    Generador ISO9660 con De-duplicación de Sectores (Base LBA: {base_lba})")
        print("========================================================================")
        print(f"[*] Directorio Origen: {root_dir}")
        print(f"[*] Nombre Volumen   : {volume_name}")
        print(f"[*] ISO Salida       : {output_iso_path}")

    # 1. Descubrimiento de directorios en Amplitud (BFS)
    # Cada entrada: (index_1based, path_absoluto, nombre_iso, parent_index_1based)
    dir_entries = []
    queue = deque([ (root_dir, "", 1) ])
    
    dirs_by_path = {}
    dir_idx = 1
    
    while queue:
        cur_p, iso_name, parent_id = queue.popleft()
        dir_entries.append((dir_idx, cur_p, iso_name, parent_id))
        dirs_by_path[cur_p] = dir_idx
        my_idx = dir_idx
        dir_idx += 1
        
        # Encontrar subdirectorios y ordenarlos alfabéticamente
        subdirs = sorted([d for d in os.listdir(cur_p) if os.path.isdir(os.path.join(cur_p, d))])
        for sub in subdirs:
            queue.append((os.path.join(cur_p, sub), sub.upper(), my_idx))

    if verbose:
        print(f"[+] Total directorios indexados (BFS ISO9660): {len(dir_entries)}")

    # 2. Construcción de Path Table en memoria
    # Type L (Little Endian) y Type M (Big Endian)
    path_table_l = bytearray()
    path_table_m = bytearray()
    
    for idx, p, name, parent in dir_entries:
        nlen = len(name) if idx > 1 else 1
        name_bytes = name.encode('ascii') if idx > 1 else b'\x00'
        
        entry_l = bytearray(8 + nlen)
        entry_l[0] = nlen
        entry_l[1] = 0 # Extended attribute record length
        # LBA provisional (offset 2..6) se rellenará más adelante
        entry_l[6:8] = parent.to_bytes(2, 'little')
        entry_l[8:8+nlen] = name_bytes
        if len(entry_l) % 2 != 0:
            entry_l.append(0)
            
        entry_m = bytearray(8 + nlen)
        entry_m[0] = nlen
        entry_m[1] = 0
        entry_m[6:8] = parent.to_bytes(2, 'big')
        entry_m[8:8+nlen] = name_bytes
        if len(entry_m) % 2 != 0:
            entry_m.append(0)
            
        path_table_l.extend(entry_l)
        path_table_m.extend(entry_m)
        
    path_table_size = len(path_table_l)
    path_table_sectors = (path_table_size + 2047) // 2048

    # 3. Planificador de Sectores LBA
    # Sector 0..15: IP.BIN (32 KB = 16 sectores)
    # Sector 16: PVD (Primary Volume Descriptor)
    # Sector 17: Volume Descriptor Set Terminator
    # Sector 18: Path Table L
    # Sector 18 + PT_sec: Path Table M
    # Sector 18 + 2*PT_sec: Root Directory y subdirectorios
    
    pvd_lba = base_lba + 16
    term_lba = base_lba + 17
    pt_l_lba = base_lba + 18
    pt_m_lba = pt_l_lba + path_table_sectors
    
    cur_lba = pt_m_lba + path_table_sectors
    
    # Asignar LBAs a cada tabla de directorio
    dir_lba_map = {}
    dir_size_map = {}
    
    # Pre-calcular tamaños de directorio
    dir_contents = {}
    for idx, p, name, parent in dir_entries:
        items = os.listdir(p)
        files = sorted([f for f in items if os.path.isfile(os.path.join(p, f))])
        subdirs = sorted([d for d in items if os.path.isdir(os.path.join(p, d))])
        dir_contents[idx] = (subdirs, files)
        
        # Calcular tamaño del directorio
        # '.' y '..' (34 + 34 = 68 bytes)
        sz = 68
        for d in subdirs:
            sz += 33 + len(d) + (1 if len(d) % 2 == 0 else 0)
        for f in files:
            iso_f = f.upper()
            if ';' not in iso_f: iso_f += ";1"
            sz += 33 + len(iso_f) + (1 if len(iso_f) % 2 == 0 else 0)
            
        dir_sectors = (sz + 2047) // 2048
        dir_lba_map[idx] = cur_lba
        dir_size_map[idx] = dir_sectors * 2048
        cur_lba += dir_sectors

    root_dir_lba = dir_lba_map[1]
    if verbose:
        print(f"[+] Root directory LBA = {root_dir_lba} (Base LBA: {base_lba})")

    # 4. Asignar LBAs a los archivos de datos (con de-duplicación por inodos)
    inode_lba_map = {}
    file_lba_map = {}
    file_size_map = {}
    
    unique_files = 0
    linked_files = 0
    saved_bytes = 0
    
    for idx, p, name, parent in dir_entries:
        subdirs, files = dir_contents[idx]
        for f in files:
            full_path = os.path.join(p, f)
            stat = os.stat(full_path)
            f_size = stat.st_size
            file_size_map[full_path] = f_size
            
            # Archivo de 0 bytes no consume sectores físicos
            if f_size == 0:
                file_lba_map[full_path] = cur_lba
                continue
                
            inode_key = (stat.st_dev, stat.st_ino)
            if inode_key in inode_lba_map:
                # ¡Hardlink detectado! Reutilizar LBA existente
                file_lba_map[full_path] = inode_lba_map[inode_key]
                linked_files += 1
                saved_bytes += f_size
            else:
                file_lba_map[full_path] = cur_lba
                inode_lba_map[inode_key] = cur_lba
                unique_files += 1
                sectors = (f_size + 2047) // 2048
                cur_lba += sectors

    total_iso_sectors = cur_lba - base_lba
    total_iso_bytes = total_iso_sectors * 2048
    
    if verbose:
        print(f"[+] Archivos únicos a escribir : {unique_files:,}")
        print(f"[+] Archivos enlazados (Hardlinks): {linked_files:,} (Ahorro: {saved_bytes/(1024*1024):.2f} MB!)")
        print(f"[+] Espacio final de la ISO    : {total_iso_bytes:,} bytes ({total_iso_bytes/(1024*1024):.2f} MB)")

    # 5. Escribir imagen ISO9660 física
    os.makedirs(os.path.dirname(os.path.abspath(output_iso_path)), exist_ok=True)
    with open(output_iso_path, 'wb') as iso_f:
        # Pre-reservar tamaño completo
        iso_f.truncate(total_iso_bytes)
        
        # Inyectar IP.BIN en los primeros 16 sectores (32 KB)
        ip_bin_path = os.path.join(root_dir, 'IP.BIN')
        if os.path.exists(ip_bin_path):
            with open(ip_bin_path, 'rb') as ip_file:
                ip_data = ip_file.read(32768)
                iso_f.seek(0)
                iso_f.write(ip_data)
                
        # Primary Volume Descriptor (PVD) a Sector 16
        pvd = bytearray(2048)
        pvd[0] = 1 # Type: PVD
        pvd[1:6] = b'CD001'
        pvd[6] = 1 # Version
        pvd[8:40] = b'SEGA SEGAKATANA '.ljust(32, b' ') # System ID
        pvd[40:72] = volume_name.encode('ascii').ljust(32, b' ') # Volume ID
        pvd[80:88] = struct.pack('<I', total_iso_sectors) + struct.pack('>I', total_iso_sectors)
        pvd[120:124] = struct.pack('<H', 1) + struct.pack('>H', 1) # Volume set size
        pvd[124:128] = struct.pack('<H', 1) + struct.pack('>H', 1) # Volume sequence number
        pvd[128:132] = struct.pack('<H', 2048) + struct.pack('>H', 2048) # Logical block size
        pvd[132:140] = struct.pack('<I', path_table_size) + struct.pack('>I', path_table_size)
        pvd[140:144] = struct.pack('<I', pt_l_lba) # Type L Path Table LBA
        pvd[148:152] = struct.pack('>I', pt_m_lba) # Type M Path Table LBA
        
        # Root directory record en PVD (34 bytes)
        root_rec = bytearray(34)
        root_rec[0] = 34
        root_rec[2:10] = struct.pack('<I', root_dir_lba) + struct.pack('>I', root_dir_lba)
        root_rec[10:18] = struct.pack('<I', dir_size_map[1]) + struct.pack('>I', dir_size_map[1])
        root_rec[25] = 2 # Directory flag
        root_rec[28:32] = struct.pack('<H', 1) + struct.pack('>H', 1)
        root_rec[32] = 1
        root_rec[33] = 0
        pvd[156:190] = root_rec
        
        pvd[190:318] = volume_name.encode('ascii').ljust(128, b' ') # Volume Set ID
        pvd[318:446] = b'SEGA ENTERPRISES'.ljust(128, b' ') # Publisher ID
        pvd[446:574] = b'SEGA ENTERPRISES'.ljust(128, b' ') # Data Preparer ID
        pvd[574:702] = b'ANTIGRAVITY MULTIDISC ENGINE'.ljust(128, b' ') # Application ID
        
        iso_f.seek((pvd_lba - base_lba) * 2048)
        iso_f.write(pvd)
        
        # Volume Descriptor Set Terminator a Sector 17
        term = bytearray(2048)
        term[0] = 255
        term[1:6] = b'CD001'
        term[6] = 1
        iso_f.seek((term_lba - base_lba) * 2048)
        iso_f.write(term)
        
        # Actualizar LBAs en las Path Tables
        pos_l = 0
        pos_m = 0
        for idx, p, name, parent in dir_entries:
            nlen = len(name) if idx > 1 else 1
            d_lba = dir_lba_map[idx]
            path_table_l[pos_l+2:pos_l+6] = struct.pack('<I', d_lba)
            path_table_m[pos_m+2:pos_m+6] = struct.pack('>I', d_lba)
            entry_len = 8 + nlen + (1 if nlen % 2 != 0 else 0)
            pos_l += entry_len
            pos_m += entry_len
            
        iso_f.seek((pt_l_lba - base_lba) * 2048)
        iso_f.write(path_table_l)
        
        iso_f.seek((pt_m_lba - base_lba) * 2048)
        iso_f.write(path_table_m)
        
        # Escribir registros de directorio
        def make_dir_record(lba, size, is_dir, name_str, is_current_dir=False, is_parent_dir=False):
            if is_current_dir:
                n_bytes = b'\x00'
            elif is_parent_dir:
                n_bytes = b'\x01'
            else:
                n_bytes = name_str.encode('ascii')
                
            nlen = len(n_bytes)
            rec_len = 33 + nlen
            if rec_len % 2 != 0:
                rec_len += 1
                
            rec = bytearray(rec_len)
            rec[0] = rec_len
            rec[2:10] = struct.pack('<I', lba) + struct.pack('>I', lba)
            rec[10:18] = struct.pack('<I', size) + struct.pack('>I', size)
            rec[25] = 2 if is_dir else 0
            rec[28:32] = struct.pack('<H', 1) + struct.pack('>H', 1)
            rec[32] = nlen
            rec[33:33+nlen] = n_bytes
            return bytes(rec)

        for idx, p, name, parent in dir_entries:
            subdirs, files = dir_contents[idx]
            d_lba = dir_lba_map[idx]
            p_lba = dir_lba_map[parent]
            
            d_block = bytearray()
            # '.' (Current Dir)
            d_block.extend(make_dir_record(d_lba, dir_size_map[idx], True, "", is_current_dir=True))
            # '..' (Parent Dir)
            d_block.extend(make_dir_record(p_lba, dir_size_map[parent], True, "", is_parent_dir=True))
            
            # Subdirectorios ordenados
            for sub in subdirs:
                sub_path = os.path.join(p, sub)
                sub_idx = dirs_by_path[sub_path]
                d_block.extend(make_dir_record(dir_lba_map[sub_idx], dir_size_map[sub_idx], True, sub.upper()))
                
            # Archivos ordenados
            for f in files:
                full_path = os.path.join(p, f)
                f_lba = file_lba_map[full_path]
                f_sz = file_size_map[full_path]
                iso_f_name = f.upper()
                if ';' not in iso_f_name: iso_f_name += ";1"
                d_block.extend(make_dir_record(f_lba, f_sz, False, iso_f_name))
                
            iso_f.seek((d_lba - base_lba) * 2048)
            iso_f.write(d_block)

        # Escribir contenido físico de los archivos
        if verbose:
            print("[*] Escribiendo contenido físico de archivos a la ISO...")
        
        written_inodes = set()
        file_count = 0
        
        for full_path, f_lba in file_lba_map.items():
            f_size = file_size_map[full_path]
            if f_size == 0:
                continue
                
            stat = os.stat(full_path)
            inode_key = (stat.st_dev, stat.st_ino)
            if inode_key in written_inodes:
                continue
            written_inodes.add(inode_key)
            
            # Posicionamiento absoluto exacto por sector LBA
            iso_f.seek((f_lba - base_lba) * 2048)
            with open(full_path, 'rb') as in_f:
                while True:
                    chunk = in_f.read(65536)
                    if not chunk: break
                    iso_f.write(chunk)
                    
            file_count += 1
            if verbose and file_count % 500 == 0:
                print(f"    [{file_count:4d}/{unique_files}] Archivos físicos escritos...")

    if verbose:
        print(f"\n[✓] ¡ISO generada con ÉXITO!")
        print(f"    - Archivo: {output_iso_path}")
        print(f"    - Tamaño : {os.path.getsize(output_iso_path):,} bytes ({os.path.getsize(output_iso_path)/(1024*1024):.2f} MB)")
        
    return True
