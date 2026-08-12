#!/usr/bin/env python3
"""
tests.py - Compilaciones de prueba y diagnóstico para el motor multidisco (Mini Puzzle Fighter y Hola Mundo).
"""

import os
import shutil
from .base import prepare_frontend_base, stage_game_files, GAMES_DIR, FRONTEND_DEFAULT_DIR
from ..core.cdi_container import build_multidisc_cdi
from ..core.iso9660 import build_iso9660_with_deduplication

def build_mini_puzzle_cdi(output_cdi_path: str, volume_name: str = "PUZZLE_FIGHTER", verbose: bool = True):
    """
    Mini-experimento: Menú interactivo Dricas + Super Puzzle Fighter II X en CDI autoboot.
    """
    staging_dir = os.path.join(os.path.dirname(os.path.abspath(output_cdi_path)), "_staging_mini_puzzle")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    if verbose:
        print("========================================================================")
        print("     Mini-Experimento: Menú Dricas + Super Puzzle Fighter II X (CDI)")
        print("========================================================================")

    # 1. Preparar Frontend con template mini_puzzle
    tpl = os.path.join(FRONTEND_DEFAULT_DIR, "DPWWW", "templates", "mini_puzzle.html")
    prepare_frontend_base(staging_dir, template_html_path=tpl)

    # 2. Agregar Super Puzzle Fighter II X
    spf_src = os.path.join(GAMES_DIR, "SPF2X")
    stage_game_files(spf_src, os.path.join(staging_dir, "TPF"))

    # 3. Compilar CDI
    res = build_multidisc_cdi(staging_dir, output_cdi_path, volume_name=volume_name, verbose=verbose)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return res

def build_mini_puzzle_gdi(output_gdi_dir: str, volume_name: str = "PUZZLE_FIGHTER", verbose: bool = True):
    """
    Mini-experimento: Menú interactivo Dricas + Super Puzzle Fighter II X en formato GDI puro.
    """
    staging_dir = os.path.join(os.path.dirname(os.path.abspath(output_gdi_dir)), "_staging_mini_gdi")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    tpl = os.path.join(FRONTEND_DEFAULT_DIR, "DPWWW", "templates", "mini_puzzle.html")
    prepare_frontend_base(staging_dir, template_html_path=tpl)
    spf_src = os.path.join(GAMES_DIR, "SPF2X")
    stage_game_files(spf_src, os.path.join(staging_dir, "TPF"))

    os.makedirs(output_gdi_dir, exist_ok=True)
    iso_path = os.path.join(output_gdi_dir, "track03.iso")
    build_iso9660_with_deduplication(staging_dir, iso_path, volume_name=volume_name, base_lba=45000, verbose=verbose)

    # Convertir a sector 2352
    t3_bin = os.path.join(output_gdi_dir, "track03.bin")
    sync = bytes.fromhex("00 FF FF FF FF FF FF FF FF FF FF 00 10 02 00 01")
    with open(iso_path, 'rb') as in_f, open(t3_bin, 'wb') as out_f:
        while True:
            chunk = in_f.read(2048)
            if not chunk: break
            out_f.write(sync + chunk.ljust(2048, b'\x00') + bytes(288))
    os.remove(iso_path)

    with open(os.path.join(output_gdi_dir, "disc.gdi"), "w") as f:
        f.write("3\n1 0 4 2352 track01.bin 0\n2 450 0 2352 track02.raw 0\n3 45000 4 2352 track03.bin 0\n")

    shutil.rmtree(staging_dir, ignore_errors=True)
    return True

def build_hola_mundo_cdi(output_cdi_path: str, volume_name: str = "HOLA_MUNDO", verbose: bool = True):
    """
    Mini-mini-experimento: Solo Browser Dricas + Hola Mundo Dreamcast.
    """
    staging_dir = os.path.join(os.path.dirname(os.path.abspath(output_cdi_path)), "_staging_hola_mundo")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    tpl = os.path.join(FRONTEND_DEFAULT_DIR, "DPWWW", "templates", "holamundo.html")
    prepare_frontend_base(staging_dir, template_html_path=tpl)

    res = build_multidisc_cdi(staging_dir, output_cdi_path, volume_name=volume_name, verbose=verbose)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return res
