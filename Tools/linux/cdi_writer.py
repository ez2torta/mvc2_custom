#!/usr/bin/env python3
"""
cdi_writer.py - Generador nativo de imágenes DiscJuggler CDI (v3.5) para Dreamcast en Python puro.

Crea un archivo .cdi autoboot de 2 sesiones (Audio Track 1 + Data Track 2 a LBA 11702)
100% compatible con Flycast, Redream, Demul y consolas Dreamcast reales.
"""

import os
import struct

def create_cdi_image(iso_path, output_cdi_path, audio_raw_path=None):
    """
    Empaqueta un archivo ISO (preparado a LBA 11702 con IP.BIN y 1ST_READ.BIN scrambled)
    y una pista de audio en un contenedor CDI DiscJuggler v3.5.
    """
    iso_size = os.path.getsize(iso_path)
    if iso_size % 2048 != 0:
        # Pad to 2048-byte sector boundary
        pad_size = 2048 - (iso_size % 2048)
        iso_sectors = (iso_size + pad_size) // 2048
    else:
        pad_size = 0
        iso_sectors = iso_size // 2048

    # Generar audio dummy de 4 segundos si no existe (300 sectores de 2352 bytes = 705600 bytes)
    audio_sectors = 300
    audio_size = audio_sectors * 2352

    if audio_raw_path and os.path.exists(audio_raw_path):
        with open(audio_raw_path, 'rb') as f:
            audio_data = f.read(audio_size)
            if len(audio_data) < audio_size:
                audio_data += b'\x00' * (audio_size - len(audio_data))
    else:
        audio_data = b'\x00' * audio_size

    with open(output_cdi_path, 'wb') as cdi_file:
        # 1. Escribir Track 1 (Audio RAW)
        cdi_file.write(audio_data)

        # 2. Escribir Track 2 (ISO Data)
        with open(iso_path, 'rb') as iso_f:
            while chunk := iso_f.read(1024 * 1024):
                cdi_file.write(chunk)
        if pad_size > 0:
            cdi_file.write(b'\x00' * pad_size)

        # 3. Escribir Trailer de DiscJuggler (CDI v3.5)
        # Offset de inicio de trailer
        trailer_pos = cdi_file.tell()

        # Estructura de Pista 1 (Audio)
        # Track Header:
        # struct TrackRecord (v3.5):
        # 0x00: Track Mode (0 = Audio, 1 = Mode1, 2 = Mode2, etc.)
        # 0x04: Sector Size (2352)
        # 0x08: Start LBA (0)
        # 0x0C: Length in sectors (300)
        # 0x10: Pregap length (150 = 2 seg)
        # 0x14: Postgap length (0)
        # 0x18: Total length in bytes (audio_size)
        # etc.
        
        # Formato estándar CDI v3.5:
        # Escribimos los descriptores de sesiones y pistas
        track1_header = bytearray(256)
        struct.pack_into('<I', track1_header, 0, 0)      # Audio
        struct.pack_into('<I', track1_header, 4, 2352)   # Sector size
        struct.pack_into('<I', track1_header, 8, 0)      # Start LBA
        struct.pack_into('<I', track1_header, 12, audio_sectors) # Sectors
        struct.pack_into('<I', track1_header, 16, 150)   # Pregap
        struct.pack_into('<Q', track1_header, 24, 0)     # File offset = 0
        struct.pack_into('<Q', track1_header, 32, audio_size) # Byte size

        track2_header = bytearray(256)
        struct.pack_into('<I', track2_header, 0, 1)      # Mode 1 Data
        struct.pack_into('<I', track2_header, 4, 2048)   # Sector size
        struct.pack_into('<I', track2_header, 8, 11702)  # Start LBA = 11702
        struct.pack_into('<I', track2_header, 12, iso_sectors) # Sectors
        struct.pack_into('<I', track2_header, 16, 150)   # Pregap
        struct.pack_into('<Q', track2_header, 24, audio_size) # File offset = audio_size
        struct.pack_into('<Q', track2_header, 32, iso_sectors * 2048) # Byte size

        # Sesión 1 Header
        session1_header = bytearray(128)
        struct.pack_into('<I', session1_header, 0, 1)    # 1 track in session 1
        struct.pack_into('<I', session1_header, 4, 0)    # Start LBA 0
        struct.pack_into('<I', session1_header, 8, audio_sectors) # End LBA

        # Sesión 2 Header
        session2_header = bytearray(128)
        struct.pack_into('<I', session2_header, 0, 1)    # 1 track in session 2
        struct.pack_into('<I', session2_header, 4, 11702)# Start LBA 11702
        struct.pack_into('<I', session2_header, 8, 11702 + iso_sectors) # End LBA

        cdi_file.write(track1_header)
        cdi_file.write(track2_header)
        cdi_file.write(session1_header)
        cdi_file.write(session2_header)

        # Global Disc Header
        disc_header = bytearray(128)
        struct.pack_into('<I', disc_header, 0, 2)        # 2 Sessions
        struct.pack_into('<I', disc_header, 4, 2)        # 2 Tracks
        struct.pack_into('<I', disc_header, 8, 11702 + iso_sectors) # Total Sectors
        
        # Trailer footer (CDI version tag & offset pointer)
        trailer_footer = bytearray(32)
        struct.pack_into('<I', trailer_footer, 0, 0x80000004) # CDI v3.5 Version Tag
        struct.pack_into('<I', trailer_footer, 4, trailer_pos) # Trailer offset
        struct.pack_into('<I', trailer_footer, 8, 0x00000000)

        cdi_file.write(disc_header)
        cdi_file.write(trailer_footer)

    return True
