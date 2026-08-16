#!/usr/bin/env python3
"""
adx_downsampler.py - Conversor y optimizador de audio CRI ADX para Sega Dreamcast.
Downsamplea pistas ADX a 22,050 Hz Mono con normalización de audio y recálculo
milimétrico de loop points (muestras y offsets de bytes), reduciendo el tamaño a ~25%
del original para permitir multijuegos de máxima capacidad en CD-R 700MB.
"""

import os
import sys
import struct
import shutil
import argparse
import subprocess
import tempfile
from typing import Dict, Optional, Tuple, List

# Diccionario global de loop points de respaldo conocidos para Dreamcast Capcom games
FALLBACK_LOOP_DICTS = {}

def load_project_looplists(search_root: str = "."):
    """Busca y carga automáticamente todos los archivos LOOPLIST.TXT en el repositorio."""
    global FALLBACK_LOOP_DICTS
    for root, _, files in os.walk(search_root):
        if ".git" in root:
            continue
        for f in files:
            if f.upper() in ("LOOPLIST.TXT", "LOOP_LIST.TXT", "LOOPS.TXT"):
                p = os.path.join(root, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        for line in fp:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            parts = line.split(":")
                            if len(parts) >= 3:
                                fname = parts[0].strip().upper()
                                l_start_str = parts[1].strip().upper()
                                l_end_str = parts[2].strip().upper()
                                title = parts[3].strip() if len(parts) > 3 else ""
                                
                                l_start = None if l_start_str in ("NO", "NONE", "", "0") and l_end_str in ("NO", "NONE", "", "0") else None
                                if l_start_str not in ("NO", "NONE", ""):
                                    try:
                                        l_start = int(l_start_str)
                                    except ValueError:
                                        pass
                                l_end = None
                                if l_end_str not in ("NO", "NONE", ""):
                                    try:
                                        l_end = int(l_end_str)
                                    except ValueError:
                                        pass
                                
                                if fname not in FALLBACK_LOOP_DICTS or (l_start is not None and l_end is not None):
                                    FALLBACK_LOOP_DICTS[fname] = {
                                        "loop_start": l_start,
                                        "loop_end": l_end,
                                        "title": title,
                                        "source_file": p
                                    }
                except Exception as e:
                    pass

def parse_adx_header(filepath: str) -> Optional[Dict]:
    """
    Parsea exhaustivamente la cabecera CRI ADX de un archivo.
    Extrae frecuencia de muestreo, canales, muestras totales y puntos de bucle (si existen).
    """
    if not os.path.isfile(filepath):
        return None
        
    try:
        with open(filepath, "rb") as f:
            header_peek = f.read(128)
            
        if len(header_peek) < 24 or header_peek[0:2] != b"\x80\x00":
            return None
            
        copy_off = struct.unpack(">H", header_peek[2:4])[0]
        data_offset = copy_off + 4
        
        enc_type = header_peek[4]
        block_size = header_peek[5]
        sample_bitdepth = header_peek[6]
        channels = header_peek[7]
        sample_rate = struct.unpack(">I", header_peek[8:12])[0]
        total_samples = struct.unpack(">I", header_peek[12:16])[0]
        highpass = struct.unpack(">H", header_peek[16:18])[0]
        version = header_peek[18]
        flags = header_peek[19]
        
        # Leer cabecera completa hasta data_offset
        with open(filepath, "rb") as f:
            full_hdr = f.read(data_offset)
            
        loop_flag = 0
        loop_start_sample = 0
        loop_start_byte = 0
        loop_end_sample = 0
        loop_end_byte = 0
        
        if len(full_hdr) >= 0x2C:
            lf = struct.unpack(">H", full_hdr[0x18:0x1A])[0]
            ls_s = struct.unpack(">I", full_hdr[0x1C:0x20])[0]
            ls_b = struct.unpack(">I", full_hdr[0x20:0x24])[0]
            le_s = struct.unpack(">I", full_hdr[0x24:0x28])[0]
            le_b = struct.unpack(">I", full_hdr[0x28:0x2C])[0]
            
            if (lf != 0 or ls_s != 0 or le_s != 0) and le_s > ls_s:
                loop_flag = 1
                loop_start_sample = ls_s
                loop_start_byte = ls_b
                loop_end_sample = le_s
                loop_end_byte = le_b
                
        return {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "file_size": os.path.getsize(filepath),
            "copy_off": copy_off,
            "data_offset": data_offset,
            "enc_type": enc_type,
            "block_size": block_size,
            "sample_bitdepth": sample_bitdepth,
            "channels": channels,
            "sample_rate": sample_rate,
            "total_samples": total_samples,
            "highpass": highpass,
            "version": version,
            "flags": flags,
            "loop_flag": loop_flag,
            "loop_start_sample": loop_start_sample,
            "loop_start_byte": loop_start_byte,
            "loop_end_sample": loop_end_sample,
            "loop_end_byte": loop_end_byte,
        }
    except Exception as e:
        return None

def build_cri_adx_header(
    sample_rate: int,
    total_samples: int,
    channels: int,
    loop_enabled: bool,
    loop_start_sample: int,
    loop_end_sample: int,
    highpass: int = 500,
    version: int = 3,
    header_align: int = 48
) -> bytes:
    """
    Construye una cabecera CRI ADX binaria canónica compatible con Sega Dreamcast.
    """
    copy_off = header_align - 4
    data_offset = header_align
    
    # Calcular offsets de byte para los loop points
    # Cada frame ADX contiene 32 muestras y ocupa 18 * channels bytes
    frame_bytes = 18 * channels
    loop_start_b = data_offset + (loop_start_sample // 32) * frame_bytes if loop_enabled else 0
    loop_end_b = data_offset + ((loop_end_sample + 31) // 32) * frame_bytes if loop_enabled else 0
    
    hdr = bytearray(data_offset)
    # 0x00: Magic 0x8000
    struct.pack_into(">H", hdr, 0x00, 0x8000)
    # 0x02: Copyright offset
    struct.pack_into(">H", hdr, 0x02, copy_off)
    # 0x04: Encoding type (3 = Standard ADX ADPCM)
    hdr[0x04] = 3
    # 0x05: Block size (18 bytes per frame)
    hdr[0x05] = 18
    # 0x06: Sample bitdepth (4-bit)
    hdr[0x06] = 4
    # 0x07: Channel count
    hdr[0x07] = channels
    # 0x08: Sample rate (Hz)
    struct.pack_into(">I", hdr, 0x08, sample_rate)
    # 0x0C: Total samples
    struct.pack_into(">I", hdr, 0x0C, total_samples)
    # 0x10: Highpass cut-off frequency (usually 500)
    struct.pack_into(">H", hdr, 0x10, highpass)
    # 0x12: Version (3)
    hdr[0x12] = version
    # 0x13: Flags (0)
    hdr[0x13] = 0
    
    # 0x14..0x2B: Loop Header
    if loop_enabled:
        struct.pack_into(">I", hdr, 0x14, 1) # Alignment / loop type
        struct.pack_into(">H", hdr, 0x18, 1) # Loop enabled = 1
        struct.pack_into(">H", hdr, 0x1A, 0) # Loop type = 0
        struct.pack_into(">I", hdr, 0x1C, loop_start_sample)
        struct.pack_into(">I", hdr, 0x20, loop_start_b)
        struct.pack_into(">I", hdr, 0x24, loop_end_sample)
        struct.pack_into(">I", hdr, 0x28, loop_end_b)
    else:
        struct.pack_into(">I", hdr, 0x14, 0)
        struct.pack_into(">H", hdr, 0x18, 0)
        struct.pack_into(">H", hdr, 0x1A, 0)
        struct.pack_into(">I", hdr, 0x1C, 0)
        struct.pack_into(">I", hdr, 0x20, 0)
        struct.pack_into(">I", hdr, 0x24, 0)
        struct.pack_into(">I", hdr, 0x28, 0)
        
    # Signature '(c)CRI' antes del fin de cabecera
    sig = b"(c)CRI"
    sig_pos = copy_off - 2
    if sig_pos >= 0 and sig_pos + len(sig) <= data_offset:
        hdr[sig_pos:sig_pos + len(sig)] = sig
        
    return bytes(hdr)

def downsample_adx_file(
    input_path: str,
    output_path: str,
    target_rate: int = 22050,
    target_channels: int = 1,
    normalize: bool = True,
    loop_start_override: Optional[int] = None,
    loop_end_override: Optional[int] = None,
    verbose: bool = False
) -> Tuple[bool, Dict]:
    """
    Convierte una pista ADX a 22050 Hz Mono, recalculando loop points y aplicando normalización.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg no se encuentra instalado en el sistema.")
        
    orig_info = parse_adx_header(input_path)
    fname_upper = os.path.basename(input_path).upper()
    
    # Determinar puntos de bucle originales
    loop_start_orig = None
    loop_end_orig = None
    loop_enabled = False
    
    # Jingles y efectos no-loopeables canónicos
    NO_LOOP_TRACKS = {"ADX_CAPL.BIN", "ADX_HERE.BIN", "ADX_OPEN.BIN", "ADX_OVER.BIN", "ADX_STAF.BIN"}
    
    if fname_upper in NO_LOOP_TRACKS:
        loop_enabled = False
    elif loop_start_override is not None and loop_end_override is not None:
        if loop_start_override != loop_end_override and loop_end_override > loop_start_override:
            loop_enabled = True
            loop_start_orig = loop_start_override
            loop_end_orig = loop_end_override
        else:
            loop_enabled = False
    elif orig_info and orig_info["loop_flag"] == 1:
        loop_enabled = True
        loop_start_orig = orig_info["loop_start_sample"]
        loop_end_orig = orig_info["loop_end_sample"]
    elif fname_upper in FALLBACK_LOOP_DICTS:
        fb = FALLBACK_LOOP_DICTS[fname_upper]
        if fb["loop_start"] is not None and fb["loop_end"] is not None and fb["loop_end"] > fb["loop_start"]:
            loop_enabled = True
            loop_start_orig = fb["loop_start"]
            loop_end_orig = fb["loop_end"]
            
    orig_rate = orig_info["sample_rate"] if orig_info else 44100
    if orig_rate <= 0:
        orig_rate = 44100
        
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_adx = os.path.join(tmpdir, "resampled.adx")
        
        # Filtros de audio: remuestreo de alta calidad + normalización
        audio_filters = []
        if normalize:
            # Normalización estándar EBU R128 (-16 LUFS, TP -1.5dB) para arcade
            audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", str(target_rate),
            "-ac", str(target_channels),
        ]
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])
        cmd.extend([
            "-c:a", "adpcm_adx",
            "-f", "adx",
            temp_adx
        ])
        
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return False, {"error": f"FFmpeg falló al procesar {input_path}: {proc.stderr}"}
            
        with open(temp_adx, "rb") as f:
            ffmpeg_raw = f.read()
            
        if len(ffmpeg_raw) < 24:
            return False, {"error": "Archivo generado por FFmpeg es inválido o muy pequeño."}
            
        ffmpeg_copy_off = struct.unpack(">H", ffmpeg_raw[2:4])[0]
        ffmpeg_data_off = ffmpeg_copy_off + 4
        new_total_samples = struct.unpack(">I", ffmpeg_raw[12:16])[0]
        audio_payload = ffmpeg_raw[ffmpeg_data_off:]
        
        # Recálculo exacto de Loop Points
        new_loop_start = 0
        new_loop_end = 0
        if loop_enabled and loop_start_orig is not None and loop_end_orig is not None:
            # Factor de escala por cambio de sample rate
            rate_factor = target_rate / float(orig_rate)
            new_loop_start = max(0, round(loop_start_orig * rate_factor))
            new_loop_end = round(loop_end_orig * rate_factor)
            if new_loop_end <= 0 or new_loop_end > new_total_samples:
                new_loop_end = new_total_samples
            if new_loop_end <= new_loop_start:
                new_loop_start = 0
                new_loop_end = new_total_samples
        else:
            loop_enabled = False
            
        # Construir cabecera CRI ADX con loop metadata
        new_header = build_cri_adx_header(
            sample_rate=target_rate,
            total_samples=new_total_samples,
            channels=target_channels,
            loop_enabled=loop_enabled,
            loop_start_sample=new_loop_start,
            loop_end_sample=new_loop_end,
            highpass=orig_info["highpass"] if orig_info else 500,
            version=3,
            header_align=48
        )
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        final_data = new_header + audio_payload
        with open(output_path, "wb") as f:
            f.write(final_data)
            
    orig_size = orig_info["file_size"] if orig_info else os.path.getsize(input_path)
    new_size = len(final_data)
    saved_bytes = orig_size - new_size
    saved_pct = (saved_bytes / orig_size * 100.0) if orig_size > 0 else 0.0
    
    stats = {
        "input_path": input_path,
        "output_path": output_path,
        "orig_size": orig_size,
        "new_size": new_size,
        "saved_bytes": saved_bytes,
        "saved_pct": saved_pct,
        "orig_rate": orig_rate,
        "new_rate": target_rate,
        "orig_channels": orig_info["channels"] if orig_info else 2,
        "new_channels": target_channels,
        "loop_enabled": loop_enabled,
        "orig_loop_start": loop_start_orig,
        "orig_loop_end": loop_end_orig,
        "new_loop_start": new_loop_start,
        "new_loop_end": new_loop_end,
        "total_samples": new_total_samples
    }
    
    if verbose:
        loop_str = f"Loop: {new_loop_start} -> {new_loop_end}" if loop_enabled else "No-Loop"
        print(f"[✓] {os.path.basename(input_path)}: {orig_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB (-{saved_pct:.1f}%) | {loop_str}")
        
    return True, stats

def batch_downsample_directory(
    input_dir: str,
    output_dir: Optional[str] = None,
    target_rate: int = 22050,
    target_channels: int = 1,
    normalize: bool = True,
    in_place: bool = False,
    backup: bool = True,
    generate_looplist: bool = True,
    verbose: bool = True
) -> Dict:
    """
    Procesa por lotes todos los archivos ADX en un directorio y sus subdirectorios.
    """
    load_project_looplists(input_dir)
    
    if in_place:
        target_out_dir = input_dir
    elif output_dir:
        target_out_dir = output_dir
    else:
        target_out_dir = input_dir + "_downsampled_22k"
        
    adx_files = []
    for root, _, files in os.walk(input_dir):
        for f in sorted(files):
            if f.upper().endswith(".ADX") or (f.upper().startswith("ADX_") and f.upper().endswith(".BIN")):
                adx_files.append(os.path.join(root, f))
                
    if not adx_files:
        if verbose:
            print(f"[!] No se encontraron archivos ADX en {input_dir}")
        return {"processed": 0, "total_orig_bytes": 0, "total_new_bytes": 0, "saved_bytes": 0}
        
    if verbose:
        print("========================================================================")
        print("    CRI ADX Downsampling & Loop Optimization Engine (22kHz Mono)")
        print("========================================================================")
        print(f"[*] Directorio de Origen: {input_dir}")
        print(f"[*] Directorio Destino  : {target_out_dir}")
        print(f"[*] Pistas encontradas  : {len(adx_files)}")
        print(f"[*] Frecuencia objetivo : {target_rate} Hz (Mono)")
        print(f"[*] Normalización EBU   : {'Activada' if normalize else 'Desactivada'}")
        print("------------------------------------------------------------------------")
        
    total_orig_bytes = 0
    total_new_bytes = 0
    success_count = 0
    fail_count = 0
    looplist_entries = []
    
    for in_file in adx_files:
        rel_path = os.path.relpath(in_file, input_dir)
        out_file = os.path.join(target_out_dir, rel_path)
        
        if in_place and backup:
            bak_file = in_file + ".orig_bak"
            if not os.path.exists(bak_file):
                shutil.copy2(in_file, bak_file)
                
        ok, stats = downsample_adx_file(
            in_file,
            out_file,
            target_rate=target_rate,
            target_channels=target_channels,
            normalize=normalize,
            verbose=verbose
        )
        
        if ok:
            success_count += 1
            total_orig_bytes += stats["orig_size"]
            total_new_bytes += stats["new_size"]
            
            # Registrar entrada para LOOPLIST.TXT
            fname = os.path.basename(out_file)
            ls = stats["new_loop_start"] if stats["loop_enabled"] else "NO"
            le = stats["new_loop_end"] if stats["loop_enabled"] else "NO"
            title = FALLBACK_LOOP_DICTS.get(fname.upper(), {}).get("title", "")
            looplist_entries.append(f"{fname}:{ls}:{le}:{title}")
        else:
            fail_count += 1
            if verbose:
                print(f"[X] Error procesando {in_file}: {stats.get('error')}")
                
    if generate_looplist and looplist_entries:
        looplist_path = os.path.join(target_out_dir, "LOOPLIST.TXT")
        with open(looplist_path, "w", encoding="utf-8") as f:
            f.write("# CRI ADX Recalculated Loop List (22050 Hz Mono)\n")
            f.write("# FILENAME:LOOP_START_SAMPLE:LOOP_END_SAMPLE:TITLE\n")
            for entry in sorted(looplist_entries):
                f.write(entry + "\n")
        if verbose:
            print(f"[✓] Archivo de puntos de bucle generado: {looplist_path}")
            
    saved_bytes = total_orig_bytes - total_new_bytes
    saved_pct = (saved_bytes / total_orig_bytes * 100.0) if total_orig_bytes > 0 else 0.0
    
    if verbose:
        print("------------------------------------------------------------------------")
        print(f"[✓] Proceso completado: {success_count} exitosos, {fail_count} fallidos")
        print(f"    Tamaño original: {total_orig_bytes/1024/1024:.2f} MB")
        print(f"    Tamaño optimizado: {total_new_bytes/1024/1024:.2f} MB")
        print(f"    Espacio liberado : {saved_bytes/1024/1024:.2f} MB ({saved_pct:.1f}% de ahorro)")
        print("========================================================================")
        
    return {
        "processed": success_count,
        "failed": fail_count,
        "total_orig_bytes": total_orig_bytes,
        "total_new_bytes": total_new_bytes,
        "saved_bytes": saved_bytes,
        "saved_pct": saved_pct
    }

def main():
    parser = argparse.ArgumentParser(description="CRI ADX Downsampling & Loop Recalculation Engine para Sega Dreamcast.")
    parser.add_argument("input", help="Archivo ADX o Directorio a procesar")
    parser.add_argument("output", nargs="?", default=None, help="Archivo o Directorio de destino")
    parser.add_argument("--rate", type=int, default=22050, help="Frecuencia de muestreo destino (default: 22050)")
    parser.add_argument("--channels", type=int, default=1, help="Canales (1=Mono, 2=Stereo, default: 1)")
    parser.add_argument("--no-normalize", action="store_true", help="Desactiva la normalización EBU R128")
    parser.add_argument("--in-place", action="store_true", help="Sobrescribe los archivos originales en su lugar")
    parser.add_argument("--no-backup", action="store_true", help="No crear copias .orig_bak al usar --in-place")
    
    args = parser.parse_args()
    
    load_project_looplists()
    
    if os.path.isfile(args.input):
        out_f = args.output or args.input
        ok, stats = downsample_adx_file(
            args.input,
            out_f,
            target_rate=args.rate,
            target_channels=args.channels,
            normalize=not args.no_normalize,
            verbose=True
        )
        sys.exit(0 if ok else 1)
    elif os.path.isdir(args.input):
        res = batch_downsample_directory(
            args.input,
            output_dir=args.output,
            target_rate=args.rate,
            target_channels=args.channels,
            normalize=not args.no_normalize,
            in_place=args.in_place,
            backup=not args.no_backup,
            verbose=True
        )
        sys.exit(0 if res["processed"] > 0 else 1)
    else:
        print(f"[!] Error: '{args.input}' no existe.")
        sys.exit(1)

if __name__ == "__main__":
    main()
