#!/usr/bin/env python3
"""
make_ipbin.py - Generador / Editor de IP.BIN para Dreamcast
Permite configurar los metadatos de un IP.BIN para juegos de Dreamcast (GDI / CDI).
"""

import sys
import os

def pad(text, length):
    return text.encode('ascii')[:length].ljust(length, b' ')

def create_custom_ipbin(template_path, output_path, title="MARVEL VS. CAPCOM 2", product="T1208N", 
                         maker="CAPCOM CO.,LTD.", bootfile="1ST_READ.BIN", is_gdi=True):
    if not os.path.exists(template_path):
        print(f"Error: No se encontró la plantilla {template_path}")
        return False

    with open(template_path, 'rb') as f:
        ip_data = bytearray(f.read())

    if len(ip_data) < 32768:
        print("Error: El archivo plantilla IP.BIN debe tener al menos 32768 bytes (32KB).")
        return False

    # Campos estándar de la cabecera SEGA (primeros 256 bytes)
    ip_data[0:16]   = pad("SEGA SEGAKATANA", 16)
    ip_data[16:32]  = pad("SEGA ENTERPRISES", 16)
    
    device_info = "GD-ROM1/1" if is_gdi else "CD-ROM1/1"
    # Los primeros 4 bytes son CRC/checksum o espacios en algunos IP.BIN
    ip_data[32:48]  = pad(f"    {device_info}", 16)
    
    ip_data[48:56]  = pad("JUE", 8)          # Región: Japón, USA, Europa (Region Free)
    ip_data[56:64]  = pad("E000010", 8)      # Periféricos (Vibration pack, VGA box, Controller, etc.)
    ip_data[64:74]  = pad(product, 10)       # Product ID
    ip_data[74:80]  = pad("V1.000", 6)       # Versión
    ip_data[80:96]  = pad("20000629", 16)    # Fecha de release
    ip_data[96:112] = pad(bootfile, 16)      # Archivo ejecutable de arranque
    ip_data[112:128]= pad(maker, 16)         # Desarrollador / Editor
    ip_data[128:256]= pad(title, 128)        # Título del juego

    with open(output_path, 'wb') as f:
        f.write(ip_data)

    print(f"[OK] IP.BIN generado exitosamente en: {output_path}")
    print(f"     Título: {title}")
    print(f"     Boot File: {bootfile}")
    print(f"     Tipo: {'GD-ROM (GDI)' if is_gdi else 'CD-ROM (CDI)'}")
    return True

if __name__ == '__main__':
    template = os.path.join(os.path.dirname(__file__), "../BootDreams-1.06c/tools/IP.BIN")
    out = os.path.join(os.path.dirname(__file__), "IP.BIN")
    create_custom_ipbin(template, out, title="MARVEL VS. CAPCOM 2", bootfile="1ST_READ.BIN", is_gdi=True)
