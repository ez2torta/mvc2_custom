#!/usr/bin/env python3
"""
base.py - Utilidades comunes y preparación del Frontend para orquestadores de compilación multijuego.
"""

import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MULTIDISC_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
REPO_ROOT = os.path.abspath(os.path.join(MULTIDISC_ROOT, "../.."))
GAMES_DIR = os.path.join(REPO_ROOT, "Games")
FRONTEND_DEFAULT_DIR = os.path.join(GAMES_DIR, "Frontend")

def prepare_frontend_base(staging_dir: str, frontend_src_dir: str = None, template_html_path: str = None):
    """
    Copia la estructura base del Frontend de Dreamcast al directorio de staging:
    - Ejecutables: 1ST_READ.BIN (Dricas), IP.BIN, XDP.INI, SG_DPLDR.BIN, MAIGO.BIN
    - Carpetas del sistema: XDPTEX, DPETC, DPFONT (con aliases de fuentes .P y .S)
    - DPWWW: Copia todo el directorio web, aplicando template_html_path si se especifica.
    """
    fe_dir = frontend_src_dir if frontend_src_dir else FRONTEND_DEFAULT_DIR

    # 1. Copiar ejecutables y configs
    for f in ['1ST_READ.BIN', 'IP.BIN', 'XDP.INI', 'SG_DPLDR.BIN', 'MAIGO.BIN']:
        src = os.path.join(fe_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(staging_dir, f))

    # 2. Copiar carpetas del sistema
    for d in ['XDPTEX', 'DPETC', 'DPFONT']:
        src = os.path.join(fe_dir, d)
        if os.path.exists(src):
            shutil.copytree(src, os.path.join(staging_dir, d), copy_function=os.link)

    # Asegurar aliases de fuentes (.P y .S)
    dpfont_dst = os.path.join(staging_dir, 'DPFONT')
    if os.path.exists(dpfont_dst):
        for p_font in os.listdir(dpfont_dst):
            if p_font.endswith('P.DAT'):
                s_font = p_font[:-5] + 'S.DAT'
                s_path = os.path.join(dpfont_dst, s_font)
                if not os.path.exists(s_path):
                    shutil.copy2(os.path.join(dpfont_dst, p_font), s_path)

    # 3. Copiar DPWWW
    dpwww_src = os.path.join(fe_dir, 'DPWWW')
    dpwww_dst = os.path.join(staging_dir, 'DPWWW')
    if os.path.exists(dpwww_src):
        shutil.copytree(dpwww_src, dpwww_dst, copy_function=os.link)
    else:
        os.makedirs(dpwww_dst, exist_ok=True)

    # Si se especificó una plantilla HTML dedicada, sobreescribir XDPDEX.HTML e INDEX.HTML
    if template_html_path and os.path.exists(template_html_path):
        with open(template_html_path, 'rb') as tf:
            content = tf.read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        for fname in ['XDPDEX.HTML', 'INDEX.HTML', 'INDEX.HTM']:
            with open(os.path.join(dpwww_dst, fname), 'wb') as out_h:
                out_h.write(content)
    else:
        # Asegurar que INDEX.HTML e INDEX.HTM sean copias exactas de XDPDEX.HTML con CRLF
        master_xdpdex = os.path.join(dpwww_dst, 'XDPDEX.HTML')
        if os.path.exists(master_xdpdex):
            with open(master_xdpdex, 'rb') as tf:
                content = tf.read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            for fname in ['XDPDEX.HTML', 'INDEX.HTML', 'INDEX.HTM']:
                with open(os.path.join(dpwww_dst, fname), 'wb') as out_h:
                    out_h.write(content)

def stage_game_files(src_dir: str, dst_dir: str, custom_1st_read: str = None):
    """
    Enlaza (mediante hardlinks) todos los archivos de un módulo de juego hacia staging.
    Si se especifica custom_1st_read, inyecta dicho ejecutable en lugar del original.
    """
    os.makedirs(dst_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        if item == '1ST_READ.BIN' and custom_1st_read:
            continue
        s_item = os.path.join(src_dir, item)
        d_item = os.path.join(dst_dir, item)
        if os.path.isfile(s_item):
            if not os.path.exists(d_item):
                os.link(s_item, d_item)

    if custom_1st_read and os.path.exists(custom_1st_read):
        d_1st = os.path.join(dst_dir, '1ST_READ.BIN')
        if os.path.exists(d_1st):
            try: os.remove(d_1st)
            except: pass
        shutil.copy2(custom_1st_read, d_1st)
