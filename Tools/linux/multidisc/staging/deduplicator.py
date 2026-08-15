#!/usr/bin/env python3
"""
deduplicator.py - Optimizador global de de-duplicación por inodos/hardlinks para directorios de staging.
"""

import os
import hashlib

def deduplicate_staging_directory(staging_dir: str, verbose: bool = True):
    """
    Escanea todos los archivos de staging, calcula su hash SHA-256
    y unifica archivos idénticos mediante hardlinks en el sistema de archivos.
    Protege los directorios del frontend (XDPTEX, DPFONT, DPWWW, DPETC) para evitar colisiones.
    """
    if verbose:
        print("[*] Ejecutando optimizador global de de-duplicación de assets...")

    hash_map = {} # sha256 -> ruta_archivo_canónico
    merged_count = 0
    saved_bytes = 0

    # Exclusiones de seguridad
    protected_dirs = {'XDPTEX', 'DPFONT', 'DPWWW', 'DPETC'}

    for root, dirs, files in os.walk(staging_dir):
        # Omitir subcarpetas protegidas del frontend
        rel_root = os.path.relpath(root, staging_dir)
        top_folder = rel_root.split(os.sep)[0]
        if top_folder in protected_dirs:
            continue

        for f in files:
            full_path = os.path.join(root, f)
            sz = os.path.getsize(full_path)
            if sz == 0:
                continue

            with open(full_path, 'rb') as hf:
                f_hash = hashlib.sha256(hf.read()).hexdigest()

            if f_hash in hash_map:
                canonical = hash_map[f_hash]
                # Si no es ya el mismo archivo físico
                if os.stat(full_path).st_ino != os.stat(canonical).st_ino:
                    os.remove(full_path)
                    os.link(canonical, full_path)
                    merged_count += 1
                    saved_bytes += sz
            else:
                hash_map[f_hash] = full_path

    if verbose:
        print(f"[+] Optimizador fusionó {merged_count:,} archivos idénticos entre juegos.")
        print(f"[+] Espacio adicional recuperado: {saved_bytes / (1024 * 1024):.2f} MB!")

    return merged_count, saved_bytes
