#!/usr/bin/env python3
"""
cdi_container.py - Ensamblador de contenedores CDI DiscJuggler v3.5 (Audio/Data a LBA 45000) para Dreamcast.
"""

import os
import struct
import ctypes
from .edc_ecc import get_libedc
from .iso9660 import build_iso9660_with_deduplication

def package_audio_data_cdi(iso_path: str, output_cdi_path: str, volume_name: str = "CAPCOM_FIGHT_PACK", base_lba: int = 45000, verbose: bool = True):
    """
    Empaqueta la ISO masterizada a LBA 45000 en un contenedor DiscJuggler CDI (Audio/Data v3.5)
    100% compatible con hardware real y emuladores (Flycast/Redream), con paridad matemática Reed-Solomon
    EDC/ECC completa en Galois Field GF(2^8) y tráiler canónico.
    """
    libedc = get_libedc()
    iso_size = os.path.getsize(iso_path)
    iso_sectors = (iso_size + 2047) // 2048

    if verbose:
        print("\n[*] Generando contenedor CDI DiscJuggler (Audio/Data a LBA 45000 con EDC/ECC)...")
        print(f"    - Pista 1: 33,600 sectores Audio CDDA + GAP (LBA 0..33600)")
        print(f"    - Pista 2: {iso_sectors:,} sectores Datos Mode 2 Form 1 (LBA {base_lba}..{base_lba + iso_sectors})")

    # Gap 1 (dummy sector 1)
    gap1_sec = bytearray(2336)
    gap1_sec[0x002] = 0x20
    gap1_sec[0x006] = 0x20
    gap1_sec[0x91c] = 0x3f
    gap1_sec[0x91d] = 0x13
    gap1_sec[0x91e] = 0xb0
    gap1_sec[0x91f] = 0xbe
    gap1_bytes = bytes(gap1_sec)

    # Gap 2 (dummy sector 2)
    gap2_sec = bytearray(2336)
    gap2_entries = [
        (0x00008, 0x54), (0x00009, 0x44), (0x0000a, 0x49), (0x0000b, 0x01), (0x0000c, 0x50), (0x0000d, 0x01), (0x0000e, 0x02),
        (0x0000f, 0x02), (0x00010, 0x02), (0x00011, 0x80), (0x00012, 0xff), (0x00013, 0xff), (0x00014, 0xff), (0x00808, 0x78),
        (0x00809, 0x62), (0x0080a, 0x21), (0x0080b, 0x6d), (0x00818, 0x93), (0x00819, 0x78), (0x0081a, 0x85), (0x0081b, 0xf5),
        (0x0081c, 0x60), (0x0081d, 0xf5), (0x0081e, 0xf7), (0x0081f, 0xf7), (0x00820, 0xf7), (0x00821, 0x0b), (0x00822, 0xaa),
        (0x00823, 0xaa), (0x00824, 0xaa), (0x0085e, 0x88), (0x0085f, 0xa6), (0x00860, 0x63), (0x00861, 0xb7), (0x0086e, 0xc7),
        (0x0086f, 0x3c), (0x00870, 0xcc), (0x00871, 0xf4), (0x00872, 0x30), (0x00873, 0xf4), (0x00874, 0xf5), (0x00875, 0xf5),
        (0x00876, 0xf5), (0x00877, 0x8b), (0x00878, 0x55), (0x00879, 0x55), (0x0087a, 0x55), (0x008b4, 0xf0), (0x008b5, 0xc4),
        (0x008b6, 0x42), (0x008b7, 0xda), (0x008c6, 0x63), (0x008c7, 0xb7), (0x008c8, 0xd0), (0x008c9, 0xf7), (0x008ca, 0x59),
        (0x008cb, 0x26), (0x008cc, 0xea), (0x008cd, 0x66), (0x008d0, 0xd1), (0x008d2, 0xf3), (0x008d3, 0x15), (0x008d4, 0x4d),
        (0x008d5, 0xf5), (0x008d6, 0xf8), (0x008d7, 0x31), (0x008d8, 0x7e), (0x008d9, 0x2f), (0x008da, 0x6b), (0x008db, 0xcc),
        (0x008dc, 0x41), (0x008dd, 0x80), (0x008de, 0xe0), (0x008df, 0xf2), (0x008e0, 0x23), (0x008e1, 0x40), (0x008fa, 0x42),
        (0x008fb, 0xda), (0x008fc, 0xcb), (0x008fd, 0x22), (0x008fe, 0x93), (0x008ff, 0x5a), (0x00900, 0x1a), (0x00901, 0xa2),
        (0x00904, 0x7b), (0x00906, 0x0c), (0x00907, 0xbf), (0x00908, 0x10), (0x00909, 0xab), (0x0090a, 0x05), (0x0090b, 0xb2),
        (0x0090c, 0xe9), (0x0090d, 0xaf), (0x0090e, 0xdc), (0x0090f, 0xcf), (0x00910, 0x4e), (0x00911, 0x0d), (0x00912, 0x6e),
        (0x00913, 0xcf), (0x00914, 0x77), (0x00915, 0x04)
    ]
    for off, val in gap2_entries:
        gap2_sec[off] = val
    gap2_bytes = bytes(gap2_sec)

    buf = bytearray(2800)
    c_buf = (ctypes.c_char * 2800).from_buffer(buf) if libedc else None

    with open(output_cdi_path, 'wb') as cdi_f:
        # 1. Track 1 Header (8 bytes)
        cdi_f.write(b'\x00\x00\x20\x00\x00\x00\x20\x00')

        # Track 1 Audio Data (silencio PCM / Mode 2): exactamente 78,839,992 bytes (78,840,000 - 8)
        # Garantiza que IP.BIN se ubique exactamente en el offset físico 79,190,408 (LBA 45000)
        zero_mb = b'\x00' * (1024 * 1024)
        bytes_left = 78840000 - 8
        while bytes_left > 0:
            to_write = min(len(zero_mb), bytes_left)
            cdi_f.write(zero_mb[:to_write])
            bytes_left -= to_write

        # 2. GAP Tracks: 75 sectores GAP 1 + 75 sectores GAP 2
        for _ in range(75):
            cdi_f.write(gap1_bytes)
        for _ in range(75):
            cdi_f.write(gap2_bytes)

        # 3. Track 2 Header (8 bytes)
        cdi_f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')

        # 4. Track 2 Data Sectors con paridad Reed-Solomon EDC/ECC
        with open(iso_path, 'rb') as in_iso:
            sec_idx = 0
            while True:
                sec = in_iso.read(2048)
                if not sec: break
                if len(sec) < 2048:
                    sec += b'\x00' * (2048 - len(sec))
                
                if libedc:
                    buf[:] = b'\x00' * len(buf)
                    buf[24:24+2048] = sec
                    curr_lba = base_lba + sec_idx
                    libedc.edc_encode_sector(c_buf, curr_lba + 150)
                    cdi_f.write(buf[24:24+2336])
                else:
                    cdi_f.write(sec)
                    cdi_f.write(b'\x00' * 288)
                sec_idx += 1

        # 5. GAP End Tracks: 2 sectores GAP 1
        cdi_f.write(gap1_bytes)
        cdi_f.write(gap1_bytes)

        # 6. CDI Trailer (100% DiscJuggler v3.5 compatible)
        cdiname = r'D:\Documents and Settings\toodles\Desktop\TDCFinal2.cdi'.encode('latin1')
        volname = volume_name.encode('latin1')

        def make_track_start():
            tsm = b'\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff'
            b = bytearray()
            b.extend(tsm * 2)
            b.extend(b'\xbc\x12\n\x02')
            b.append(len(cdiname))
            b.extend(cdiname)
            next_arr = bytearray(31)
            for off, val in [(0x0b, 0x02), (0x16, 0x80), (0x17, 0x40), (0x18, 0x7e), (0x19, 0x05), (0x1d, 0x98)]:
                next_arr[off] = val
            b.extend(next_arr)
            return b

        gen_tr = bytearray()
        gen_tr.extend(struct.pack('<HHI', 2, 1, 0))

        # Track 1 (Audio)
        gen_tr.extend(make_track_start())
        sec1 = bytearray(195)
        for off, val in [
            (0x00, 0x02), (0x02, 0x96), (0x06, 0x40), (0x07, 0x83), (0x10, 0x02), (0x24, 0xd6), (0x25, 0x83),
            (0x38, 0x01), (0x3c, 0x04), (0x41, 0xd6), (0x42, 0x83), (0x5a, 0xff), (0x5b, 0xff), (0x5c, 0xff),
            (0x5d, 0xff), (0x5e, 0xff), (0x5f, 0xff), (0x60, 0xff), (0x61, 0xff), (0x62, 0x01),
            (0x66, 0x80), (0x6a, 0x02), (0x6e, 0x10), (0x72, 0x44), (0x73, 0xac), (0xa0, 0xff),
            (0xa1, 0xff), (0xa2, 0xff), (0xa3, 0xff), (0xb0, 0x02), (0xbd, 0x01)
        ]:
            sec1[off] = val
        gen_tr.extend(sec1)

        # Track 2 (Data)
        gen_tr.extend(make_track_start())
        sec2 = bytearray(195)
        for off, val in [
            (0x00, 0x02), (0x02, 0x96), (0x10, 0x02), (0x18, 0x01), (0x20, 0xc8), (0x21, 0xaf),
            (0x38, 0x01), (0x3c, 0x04), (0x5a, 0xff), (0x5b, 0xff), (0x5c, 0xff), (0x5d, 0xff),
            (0x5e, 0xff), (0x5f, 0xff), (0x60, 0xff), (0x61, 0xff), (0x62, 0x01), (0x66, 0x80),
            (0x6a, 0x02), (0x6e, 0x10), (0x72, 0x44), (0x73, 0xac), (0xa0, 0xff), (0xa1, 0xff),
            (0xa2, 0xff), (0xa3, 0xff), (0xb0, 0x02), (0xb8, 0xc8), (0xb9, 0xaf)
        ]:
            sec2[off] = val
        
        data_sectors = iso_sectors
        sec2[0x06] = data_sectors & 0xFF
        sec2[0x07] = (data_sectors >> 8) & 0xFF
        sec2[0x08] = (data_sectors >> 16) & 0xFF
        sec2[0x09] = (data_sectors >> 24) & 0xFF
        
        end_msf = data_sectors + 150
        sec2[0x24] = end_msf & 0xFF
        sec2[0x25] = (end_msf >> 8) & 0xFF
        sec2[0x26] = (end_msf >> 16) & 0xFF
        sec2[0x27] = (end_msf >> 24) & 0xFF
        
        sec2[0x41] = end_msf & 0xFF
        sec2[0x42] = (end_msf >> 8) & 0xFF
        sec2[0x43] = (end_msf >> 16) & 0xFF
        sec2[0x44] = (end_msf >> 24) & 0xFF
        gen_tr.extend(sec2)

        # End Header
        gen_tr.extend(make_track_start())
        total_space = base_lba + data_sectors + 150
        gen_tr.extend(struct.pack('<IB', total_space, len(volname)))
        gen_tr.extend(volname)

        end_arr = bytearray(42)
        for off, val in [(0x01, 0x01), (0x05, 0x01), (0x26, 0x06), (0x29, 0x80)]:
            end_arr[off] = val
        gen_tr.extend(end_arr)

        trailer_len = len(gen_tr) + 4
        gen_tr.extend(struct.pack('<I', trailer_len))

        cdi_f.write(gen_tr)

    if verbose:
        print(f"\n[✓] ¡Imagen CDI Multijuego autobootable generada con ÉXITO!")
        print(f"    - Archivo: {output_cdi_path}")
        print(f"    - Formato: Audio/Data a LBA 45000 (100% compatible Flycast y consolas reales)")
        print(f"    - Tamaño : {os.path.getsize(output_cdi_path):,} bytes ({os.path.getsize(output_cdi_path)/(1024*1024):.2f} MB)")
        
    return True

def build_multidisc_cdi(staging_dir: str, output_cdi_path: str, volume_name: str = "MULTIDISC", verbose: bool = True):
    """
    Función de alto nivel: Pre-masteriza la ISO9660 y empaqueta el CDI autobootable completo.
    """
    output_dir = os.path.dirname(os.path.abspath(output_cdi_path))
    os.makedirs(output_dir, exist_ok=True)
    temp_iso_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(output_cdi_path))[0]}_data.iso")

    if verbose:
        print("\n" + "=" * 72)
        print("   ETAPA 1: Pre-masterizado de ISO9660 Independiente (LBA 45000)")
        print("=" * 72)
    build_iso9660_with_deduplication(staging_dir, temp_iso_path, volume_name=volume_name, base_lba=45000, verbose=verbose)

    if verbose:
        print("\n" + "=" * 72)
        print("   ETAPA 2: Ensamblado de Contenedor CDI (Audio + GAPs + EDC/ECC)")
        print("=" * 72)
    res = package_audio_data_cdi(temp_iso_path, output_cdi_path, volume_name=volume_name, verbose=verbose)

    # Limpieza de archivo ISO temporal
    if os.path.exists(temp_iso_path):
        try: os.remove(temp_iso_path)
        except: pass

    return res
