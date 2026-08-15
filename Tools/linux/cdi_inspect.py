#!/usr/bin/env python3
"""
cdi_inspect.py - Inspector de estructura CDI DiscJuggler para Dreamcast.

Uso:
    python3 cdi_inspect.py archivo.cdi [archivo2.cdi ...]
    python3 cdi_inspect.py *.cdi
    python3 cdi_inspect.py archivo.cdi --hex    # Dump hex completo del trailer
"""

import struct
import sys
import os

SECTOR_SIZES = {2048: "Mode1/2048", 2336: "Mode2/2336", 2352: "Raw/2352", 2368: "Raw+Sub/2368", 2448: "Raw+Full/2448"}
TRACK_MODES = {0: "Audio", 1: "Mode1", 2: "Mode2"}

def inspect_cdi(path, hex_dump=False):
    fsize = os.path.getsize(path)
    
    with open(path, 'rb') as f:
        # 1. Leer trailer length (últimos 4 bytes)
        f.seek(-4, 2)
        trailer_len = struct.unpack('<I', f.read(4))[0]
        
        if trailer_len > fsize or trailer_len < 20:
            print(f"  [ERROR] Trailer length inválido: {trailer_len}")
            return
        
        # 2. Leer trailer completo
        trailer_start = fsize - trailer_len
        f.seek(trailer_start)
        trailer = f.read(trailer_len)
        
        # 3. Buscar SEGA SEGAKATANA en el archivo
        sega_offsets = []
        f.seek(0)
        search_positions = [0, 350000, 1060000, 1413000, 79190000]
        for sp in search_positions:
            if sp >= fsize:
                continue
            f.seek(sp)
            chunk = f.read(500000)
            idx = 0
            while True:
                pos = chunk.find(b'SEGA SEGAKATANA', idx)
                if pos < 0:
                    break
                abs_pos = sp + pos
                if abs_pos not in sega_offsets:
                    sega_offsets.append(abs_pos)
                idx = pos + 1
        
        # 4. Parsear el trailer
        print(f"  Tamaño archivo : {fsize:,} bytes ({fsize/(1024*1024):.1f} MB)")
        print(f"  Trailer        : {trailer_len} bytes @ offset {trailer_start:,}")
        print(f"  Header (8B)    : {trailer[:8].hex()}")
        
        # 5. Encontrar track_start_marks
        mark = b'\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff'
        positions = []
        pos = 0
        while True:
            idx = trailer.find(mark, pos)
            if idx < 0:
                break
            positions.append(idx)
            pos = idx + 1
        
        print(f"  Marks encontrados: {len(positions)} (= {len(positions)//2} tracks + end)")
        
        # 6. Parsear cada track (pares de marks)
        tracks = []
        file_offset = 0  # Acumulador de posición en el archivo
        
        for i in range(0, len(positions) - 1, 2):
            desc_start = positions[i + 1] + 10  # Después del segundo mark
            
            if desc_start + 5 > len(trailer):
                break
            
            ver = trailer[desc_start:desc_start + 4]
            namelen = trailer[desc_start + 4]
            name_end = desc_start + 5 + namelen
            name = trailer[desc_start + 5:name_end].decode('latin1', errors='replace')
            
            next_block_start = name_end
            next_block = trailer[next_block_start:next_block_start + 31]
            sec_start = next_block_start + 31
            
            if sec_start + 195 > len(trailer):
                # Este es el end marker
                # Parsear end data: total_space(4) + volnamelen(1) + volname
                end_data = trailer[sec_start - 31:]
                # El end marker no tiene next_block de 31 bytes en el mismo sentido
                # Busquemos el total_space y volume name después del name
                after_name = trailer[name_end:]
                # next_block(31) + total_space(4) + volnamelen(1) + volname + end(42)
                if len(after_name) >= 31 + 4 + 1:
                    ts_off = 31
                    total_space = struct.unpack('<I', after_name[ts_off:ts_off + 4])[0]
                    vn_len = after_name[ts_off + 4]
                    vol_name = after_name[ts_off + 5:ts_off + 5 + vn_len].decode('latin1', errors='replace')
                    print(f"\n  End Header:")
                    print(f"    Total space  : {total_space:,} sectores")
                    print(f"    Volume name  : '{vol_name}'")
                break
            
            sec = trailer[sec_start:sec_start + 195]
            
            sector_count = struct.unpack('<I', sec[0x06:0x0a])[0]
            start_lba = struct.unpack('<I', sec[0x20:0x24])[0]
            end_msf = struct.unpack('<I', sec[0x24:0x28])[0]
            start_lba_b = struct.unpack('<I', sec[0xb8:0xbc])[0]
            
            # Detectar tipo de sector y modo
            val_00 = sec[0x00]
            val_02 = sec[0x02]  # pregap?
            val_10 = sec[0x10]
            val_18 = sec[0x18]  # session flag
            val_38 = sec[0x38]
            val_3c = sec[0x3c]
            
            # Sector size detection from the 31-byte next_block
            # next_block[0x0b] might encode something about sector size
            nb_0b = next_block[0x0b] if len(next_block) > 0x0b else 0
            
            track_num = i // 2 + 1
            
            # Determinar sector size basado en el context
            # En CDI, el sector size se puede inferir del modo
            if val_38 == 0x00:
                sec_size = 2352
                mode_str = "Audio CDDA"
            elif val_38 == 0x01:
                sec_size = 2336 if val_3c == 0x04 else 2048
                mode_str = f"Mode2/Form1 ({sec_size}B)"
            elif val_38 == 0x02:
                sec_size = 2352
                mode_str = "Audio/Raw (2352B)"
            else:
                sec_size = 2336
                mode_str = f"Unknown mode 0x{val_38:02x}"
            
            # Calcular tamaño raw en archivo
            raw_track_size = sector_count * sec_size
            
            track_info = {
                'num': track_num,
                'sectors': sector_count,
                'start_lba': start_lba,
                'start_lba_b': start_lba_b,
                'end_msf': end_msf,
                'sec_size': sec_size,
                'mode_str': mode_str,
                'session_flag': val_18,
                'raw_size': raw_track_size,
                'file_offset': file_offset,
                'val_00': val_00,
                'val_02': val_02,
                'val_10': val_10,
                'val_38': val_38,
                'val_3c': val_3c,
            }
            tracks.append(track_info)
            file_offset += raw_track_size
            
            # Imprimir info del track
            session = "Sesión 2" if val_18 else "Sesión 1"
            print(f"\n  Track {track_num} ({session}):")
            print(f"    Modo         : {mode_str}")
            print(f"    Sectores     : {sector_count:,}")
            print(f"    Tamaño raw   : {raw_track_size:,} bytes ({raw_track_size/(1024*1024):.2f} MB)")
            print(f"    Start LBA    : {start_lba} (0x{start_lba:08x})")
            if start_lba_b and start_lba_b != start_lba:
                print(f"    Start LBA (B): {start_lba_b} (0x{start_lba_b:08x})")
            print(f"    End MSF      : {end_msf}")
            print(f"    Offset archivo: {track_info['file_offset']:,}")
            print(f"    Descriptor   : [00]={val_00:#04x} [02]={val_02:#04x} [10]={val_10:#04x} [18]={val_18:#04x} [38]={val_38:#04x} [3c]={val_3c:#04x}")
            
            if hex_dump:
                print(f"    sec[00-0f]: {sec[0x00:0x10].hex()}")
                print(f"    sec[10-1f]: {sec[0x10:0x20].hex()}")
                print(f"    sec[20-2f]: {sec[0x20:0x30].hex()}")
                print(f"    sec[30-3f]: {sec[0x30:0x40].hex()}")
                print(f"    sec[40-4f]: {sec[0x40:0x50].hex()}")
                print(f"    sec[b0-c2]: {sec[0xb0:0xc3].hex()}")
                print(f"    next_blk : {next_block.hex()}")
        
        # 7. Validación: verificar que SEGA está donde debería
        print(f"\n  === Validación ===")
        if sega_offsets:
            print(f"  SEGA SEGAKATANA encontrado en offsets: {sega_offsets}")
        
        # Calcular dónde debería estar el data track según el trailer
        if len(tracks) >= 2:
            t1 = tracks[0]
            t2 = tracks[1]
            
            # El data track debería estar después del audio + gaps
            gap_size = 150 * 2336  # 75+75 sectores de gap
            expected_data_offset = t1['raw_size'] + gap_size + 8  # +8 track header
            
            print(f"  Audio track raw: {t1['raw_size']:,} bytes")
            print(f"  + GAPs (150×2336): {gap_size:,} bytes")
            print(f"  + Track2 header: 8 bytes")
            print(f"  = Data esperado en offset: {expected_data_offset:,}")
            
            if sega_offsets:
                actual = sega_offsets[0]
                # SEGA está dentro del primer sector Mode2: offset 0 o 8 (subheader)
                for adj in [0, 8]:
                    if actual - adj == expected_data_offset:
                        print(f"  ✅ SEGA en {actual} = esperado + {adj} (subheader)")
                        break
                else:
                    diff = actual - expected_data_offset
                    print(f"  ❌ SEGA en {actual}, esperado ~{expected_data_offset} (diff: {diff:+,})")
                    if abs(diff) == 352800:
                        print(f"     → Diferencia = 352,800 = cdi4dc file_header (layout cdi4dc != Python writer)")
        
        # Capacidad CD-R
        if tracks:
            last = tracks[-1]
            total_sectors = last['start_lba'] + last['sectors']
            pct = total_sectors / 360000 * 100
            fits = "✅ Cabe" if pct <= 100 else "❌ NO cabe"
            print(f"\n  Capacidad CD-R : {total_sectors:,} / 360,000 sectores ({pct:.1f}%) {fits}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 cdi_inspect.py <archivo.cdi> [archivo2.cdi ...] [--hex]")
        sys.exit(1)
    
    hex_dump = '--hex' in sys.argv
    files = [f for f in sys.argv[1:] if f != '--hex']
    
    for path in files:
        if not os.path.exists(path):
            print(f"\n{'='*72}")
            print(f"  {path}: NO ENCONTRADO")
            continue
        
        print(f"\n{'='*72}")
        print(f"  📀 {os.path.basename(path)}")
        print(f"{'='*72}")
        
        try:
            inspect_cdi(path, hex_dump)
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    print()


if __name__ == '__main__':
    main()
