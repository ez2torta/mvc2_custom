#!/usr/bin/env python3
"""
edc_ecc.py - Interfaz nativa para cálculo de paridad Reed-Solomon EDC/ECC para Dreamcast.
"""

import os
import ctypes
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MULTIDISC_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REPO_ROOT = os.path.abspath(os.path.join(MULTIDISC_ROOT, "../.."))
LIBEDC_PATH = os.path.join(MULTIDISC_ROOT, "libedc.so")

def get_libedc():
    """Carga o compila dinámicamente la biblioteca de paridad Reed-Solomon EDC/ECC."""
    if not os.path.exists(LIBEDC_PATH):
        src_dir = os.path.join(REPO_ROOT, 'Tools', 'src', 'cdi4dc', 'edc')
        if os.path.exists(src_dir):
            cmd = [
                'gcc', '-O2', '-fPIC', f'-I{src_dir}/inc',
                f'{src_dir}/src/edc_ecc.c', f'{src_dir}/src/libedc.c', f'{src_dir}/src/patch.c',
                '-shared', '-o', LIBEDC_PATH
            ]
            subprocess.run(cmd, check=True)
    if os.path.exists(LIBEDC_PATH):
        lib = ctypes.CDLL(LIBEDC_PATH)
        lib.edc_encode_sector.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        lib.edc_encode_sector.restype = ctypes.c_int
        return lib
    return None
