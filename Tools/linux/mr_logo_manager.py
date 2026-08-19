#!/usr/bin/env python3
"""
mr_logo_manager.py - Gestor de MR Logos y Metadatos de IP.BIN para Sega Dreamcast
================================================================================
Permite extraer, crear e inyectar el logotipo MR ("Media Research Logo") que se muestra
en la pantalla de licencia de SEGA durante el arranque de la Dreamcast, tanto para
Marvel vs Capcom 2 Standalone como para el disco Multijuegos (Frontend).
"""

import sys
import os
import argparse
import struct
from PIL import Image

MR_OFFSET = 0x226C
MAX_MR_SIZE = 32768 - MR_OFFSET  # 23,956 bytes max

def pad(text, length):
    return text.encode('ascii', errors='ignore')[:length].ljust(length, b' ')

def get_ip_info(ip_path):
    if not os.path.exists(ip_path):
        return None
    data = open(ip_path, 'rb').read()
    if len(data) < 32768:
        return None
        
    hardware = data[0:16].decode('ascii', errors='ignore').strip()
    maker = data[16:32].decode('ascii', errors='ignore').strip()
    device = data[32:48].decode('ascii', errors='ignore').strip()
    region = data[48:56].decode('ascii', errors='ignore').strip()
    product = data[64:74].decode('ascii', errors='ignore').strip()
    version = data[74:80].decode('ascii', errors='ignore').strip()
    date = data[80:96].decode('ascii', errors='ignore').strip()
    bootfile = data[96:112].decode('ascii', errors='ignore').strip()
    software_maker = data[112:128].decode('ascii', errors='ignore').strip()
    title = data[128:256].decode('ascii', errors='ignore').strip()
    
    mr_present = False
    mr_info = None
    if len(data) >= MR_OFFSET + 30 and data[MR_OFFSET:MR_OFFSET+2] == b'MR':
        mr_present = True
        mr_size = struct.unpack('<H', data[MR_OFFSET+2:MR_OFFSET+4])[0]
        w = struct.unpack('<H', data[MR_OFFSET+10:MR_OFFSET+12])[0]
        h = struct.unpack('<H', data[MR_OFFSET+14:MR_OFFSET+16])[0]
        pos_x = struct.unpack('<H', data[MR_OFFSET+18:MR_OFFSET+20])[0]
        pos_y = struct.unpack('<H', data[MR_OFFSET+22:MR_OFFSET+24])[0]
        num_colors = struct.unpack('<H', data[MR_OFFSET+26:MR_OFFSET+28])[0]
        mr_info = {
            'size': mr_size, 'width': w, 'height': h,
            'pos_x': pos_x, 'pos_y': pos_y, 'num_colors': num_colors
        }
        
    return {
        'hardware': hardware, 'maker': maker, 'device': device,
        'region': region, 'product': product, 'version': version,
        'date': date, 'bootfile': bootfile, 'software_maker': software_maker,
        'title': title, 'mr_present': mr_present, 'mr_info': mr_info
    }

def encode_image_to_mr(image_path, pos_x=12, pos_y=16, max_colors=16):
    img = Image.open(image_path)
    if img.mode != 'P':
        img = img.convert('RGB').quantize(colors=max_colors)
        
    w, h = img.size
    palette_raw = img.getpalette()
    num_colors = min(len(palette_raw) // 3 if palette_raw else 0, 256)
    if num_colors == 0:
        num_colors = 1
        palette_raw = [0, 0, 0]
        
    mr_palette = bytearray()
    for i in range(num_colors):
        r = palette_raw[i*3] if i*3 < len(palette_raw) else 0
        g = palette_raw[i*3 + 1] if i*3 + 1 < len(palette_raw) else 0
        b = palette_raw[i*3 + 2] if i*3 + 2 < len(palette_raw) else 0
        mr_palette.extend([r, g, b, 0])
        
    try:
        pixels = list(img.get_flattened_data())
    except AttributeError:
        pixels = list(img.getdata())
        
    mr_data = bytearray()
    i = 0
    total = len(pixels)
    while i < total:
        color = pixels[i]
        run_len = 1
        while i + run_len < total and pixels[i + run_len] == color and run_len < 255:
            run_len += 1
            
        if run_len > 1:
            if run_len <= 127:
                mr_data.extend([0x80 | run_len, color])
            else:
                mr_data.extend([0x82, run_len, color])
            i += run_len
        else:
            if color < 0x80:
                mr_data.append(color)
            else:
                mr_data.extend([0x81, color])
            i += 1
            
    header_size = 30 + len(mr_palette)
    total_size = header_size + len(mr_data)
    
    header = bytearray(30)
    header[0:2] = b'MR'
    header[2:4] = struct.pack('<H', total_size)
    header[10:12] = struct.pack('<H', w)
    header[14:16] = struct.pack('<H', h)
    header[18:20] = struct.pack('<H', pos_x)
    header[22:24] = struct.pack('<H', pos_y)
    header[26:28] = struct.pack('<H', num_colors)
    
    full_mr = bytes(header + mr_palette + mr_data)
    if len(full_mr) > MAX_MR_SIZE:
        raise ValueError(f"El tamaño del MR generado ({len(full_mr)} bytes) excede el máximo permitido ({MAX_MR_SIZE} bytes).")
    return full_mr

def decode_mr_to_png(mr_bytes, output_png_path):
    if mr_bytes[:2] != b'MR':
        raise ValueError("Los datos no tienen la cabecera mágica 'MR'.")
    size = struct.unpack('<H', mr_bytes[2:4])[0]
    w = struct.unpack('<H', mr_bytes[10:12])[0]
    h = struct.unpack('<H', mr_bytes[14:16])[0]
    num_colors = struct.unpack('<H', mr_bytes[26:28])[0]
    
    palette_data = mr_bytes[30:30 + num_colors*4]
    palette = []
    for i in range(num_colors):
        palette.extend([palette_data[i*4], palette_data[i*4 + 1], palette_data[i*4 + 2]])
    while len(palette) < 768:
        palette.extend([0, 0, 0])
        
    img_data = mr_bytes[30 + num_colors*4:size]
    pixels = []
    i = 0
    total_pixels = w * h
    while i < len(img_data) and len(pixels) < total_pixels:
        b = img_data[i]
        i += 1
        if b == 0x82:
            count = img_data[i]
            i += 1
            color = img_data[i]
            i += 1
            pixels.extend([color] * count)
        elif b > 0x80:
            count = b - 0x80
            color = img_data[i]
            i += 1
            pixels.extend([color] * count)
        else:
            pixels.append(b)
            
    img = Image.new('P', (w, h))
    img.putpalette(palette)
    img.putdata(pixels[:total_pixels])
    img.save(output_png_path)
    return w, h, num_colors

def inject_mr_into_ipbin(ip_path, mr_data):
    if not os.path.exists(ip_path):
        raise FileNotFoundError(f"No existe el archivo {ip_path}")
    data = bytearray(open(ip_path, 'rb').read())
    if len(data) < 32768:
        raise ValueError(f"{ip_path} debe tener 32768 bytes (32 KB).")
        
    # Limpiar sector MR anterior
    data[MR_OFFSET:32768] = b'\x00' * (32768 - MR_OFFSET)
    # Escribir nuevo MR
    data[MR_OFFSET:MR_OFFSET+len(mr_data)] = mr_data
    
    with open(ip_path, 'wb') as f:
        f.write(data)

def main():
    parser = argparse.ArgumentParser(description="Gestor de MR Logo y Metadatos de IP.BIN para Sega Dreamcast")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # info
    p_info = subparsers.add_parser("info", help="Muestra la información y estado del MR logo en un IP.BIN")
    p_info.add_argument("ip_file", help="Ruta al archivo IP.BIN")
    
    # extract
    p_ext = subparsers.add_parser("extract", help="Extrae el MR Logo de un IP.BIN a imagen PNG")
    p_ext.add_argument("ip_file", help="Ruta al archivo IP.BIN")
    p_ext.add_argument("output_png", help="Ruta donde guardar el PNG")
    
    # encode
    p_enc = subparsers.add_parser("encode", help="Convierte un archivo de imagen (PNG/BMP/JPG) a formato .mr")
    p_enc.add_argument("input_image", help="Ruta a la imagen de entrada")
    p_enc.add_argument("output_mr", help="Ruta al archivo .mr de salida")
    p_enc.add_argument("--pos-x", type=int, default=12, help="Posición horizontal en pantalla (def: 12)")
    p_enc.add_argument("--pos-y", type=int, default=16, help="Posición vertical en pantalla (def: 16)")
    p_enc.add_argument("--colors", type=int, default=16, help="Número de colores (def: 16, max: 256)")
    
    # inject
    p_inj = subparsers.add_parser("inject", help="Inyecta un logo (.png o .mr) en uno o más archivos IP.BIN")
    p_inj.add_argument("image_or_mr", help="Ruta a la imagen (.png/.jpg/.bmp) o archivo .mr")
    p_inj.add_argument("--targets", nargs="+", help="Rutas de IP.BIN destino (opcional)")
    p_inj.add_argument("--all", action="store_true", help="Inyecta automáticamente en MVC2 y Multijuegos (Games/Frontend/IP.BIN)")
    p_inj.add_argument("--pos-x", type=int, default=12, help="Posición X")
    p_inj.add_argument("--pos-y", type=int, default=16, help="Posición Y")
    p_inj.add_argument("--colors", type=int, default=16, help="Máximo de colores")
    
    # set-meta
    p_meta = subparsers.add_parser("set-meta", help="Modifica metadatos de texto en un IP.BIN")
    p_meta.add_argument("ip_file", help="Ruta al archivo IP.BIN")
    p_meta.add_argument("--title", help="Título del juego (max 128 chars)")
    p_meta.add_argument("--maker", help="Nombre del desarrollador (max 16 chars)")
    p_meta.add_argument("--product", help="ID de Producto (max 10 chars)")
    p_meta.add_argument("--bootfile", help="Ejecutable de arranque (max 16 chars)")
    p_meta.add_argument("--region", default="JUE", help="Código de región (def: JUE)")
    
    args = parser.parse_args()
    
    if args.command == "info":
        info = get_ip_info(args.ip_file)
        if not info:
            print(f"[!] Error: No se pudo leer {args.ip_file}")
            sys.exit(1)
        print(f"============================================================")
        print(f" Metadatos de {args.ip_file}")
        print(f"============================================================")
        print(f" Título         : {info['title']}")
        print(f" Desarrollador  : {info['software_maker']}")
        print(f" ID de Producto : {info['product']}")
        print(f" Versión        : {info['version']}")
        print(f" Región         : {info['region']}")
        print(f" Boot File      : {info['bootfile']}")
        print(f" Hardware / Dev : {info['hardware']} / {info['device']}")
        print(f"------------------------------------------------------------")
        if info['mr_present']:
            mr = info['mr_info']
            print(f" MR Boot Logo   : PRESENTE [✓]")
            print(f"   Dimensiones  : {mr['width']} x {mr['height']} píxeles")
            print(f"   Posición X,Y : ({mr['pos_x']}, {mr['pos_y']})")
            print(f"   Colores      : {mr['num_colors']} colores")
            print(f"   Tamaño MR    : {mr['size']} bytes")
        else:
            print(f" MR Boot Logo   : No presente o sector vacío")
        print(f"============================================================")
        
    elif args.command == "extract":
        info = get_ip_info(args.ip_file)
        if not info or not info['mr_present']:
            print(f"[!] Error: No hay MR logo en {args.ip_file}")
            sys.exit(1)
        data = open(args.ip_file, 'rb').read()[MR_OFFSET:]
        w, h, cols = decode_mr_to_png(data, args.output_png)
        print(f"[✓] MR logo extraído con éxito a: {args.output_png} ({w}x{h}, {cols} colores)")
        
    elif args.command == "encode":
        mr_bytes = encode_image_to_mr(args.input_image, args.pos_x, args.pos_y, args.colors)
        with open(args.output_mr, 'wb') as f:
            f.write(mr_bytes)
        print(f"[✓] Logo codificado exitosamente a: {args.output_mr} ({len(mr_bytes)} bytes)")
        
    elif args.command == "inject":
        if args.image_or_mr.lower().endswith('.mr'):
            mr_bytes = open(args.image_or_mr, 'rb').read()
        else:
            mr_bytes = encode_image_to_mr(args.image_or_mr, args.pos_x, args.pos_y, args.colors)
            
        targets = []
        if args.all:
            default_targets = [
                'MVC2/IP.BIN',
                'Games/Frontend/IP.BIN',
                'output_gdi/IP.BIN',
                'Games/MVC2_Vanilla/IP.BIN'
            ]
            for t in default_targets:
                if os.path.exists(t):
                    targets.append(t)
        elif args.targets:
            targets = args.targets
        else:
            print("[!] Error: Especifica --targets <archivos> o usa --all")
            sys.exit(1)
            
        for t in targets:
            inject_mr_into_ipbin(t, mr_bytes)
            print(f"[✓] MR Logo inyectado exitosamente en: {t}")
            
    elif args.command == "set-meta":
        data = bytearray(open(args.ip_file, 'rb').read())
        if args.title: data[128:256] = pad(args.title, 128)
        if args.maker: data[112:128] = pad(args.maker, 16)
        if args.product: data[64:74] = pad(args.product, 10)
        if args.bootfile: data[96:112] = pad(args.bootfile, 16)
        if args.region: data[48:56] = pad(args.region, 8)
        with open(args.ip_file, 'wb') as f:
            f.write(data)
        print(f"[✓] Metadatos actualizados exitosamente en: {args.ip_file}")

if __name__ == '__main__':
    main()
