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

def safe_link_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)

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
            shutil.copytree(src, os.path.join(staging_dir, d), copy_function=safe_link_or_copy)

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
        shutil.copytree(dpwww_src, dpwww_dst, copy_function=safe_link_or_copy)
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
    Enlaza (mediante hardlinks) todos los archivos y subdirectorios de un módulo de juego hacia staging.
    Si se especifica custom_1st_read, inyecta dicho ejecutable en lugar del original.
    """
    os.makedirs(dst_dir, exist_ok=True)
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        d_root = os.path.join(dst_dir, rel) if rel != '.' else dst_dir
        os.makedirs(d_root, exist_ok=True)
        for f in files:
            if rel == '.' and f == '1ST_READ.BIN' and custom_1st_read:
                continue
            s_f = os.path.join(root, f)
            d_f = os.path.join(d_root, f)
            if not os.path.exists(d_f):
                try:
                    os.link(s_f, d_f)
                except OSError:
                    shutil.copy2(s_f, d_f)

    if custom_1st_read and os.path.exists(custom_1st_read):
        d_1st = os.path.join(dst_dir, '1ST_READ.BIN')
        if os.path.exists(d_1st):
            try: os.remove(d_1st)
            except: pass
        shutil.copy2(custom_1st_read, d_1st)

def retarget_staged_binaries_for_lba(staging_dir: str, target_lba: int = 11702, verbose: bool = True):
    """
    Parchea dinámicamente las referencias a FAD de PVD y Track en ejecutables SH-4 (1ST_READ.BIN, SG_DPLDR.BIN,
    MAIGO.BIN, 2_DP.BIN, etc.) y la cabecera IP.BIN para alinearlos al LBA destino (11702 o 45000).
    Rompe hardlinks antes de modificar para proteger los archivos originales en Games/.
    """
    import struct
    target_fad_pvd = target_lba + 166
    target_fad_trk = target_lba + 150
    target_pvd_bytes = struct.pack('<I', target_fad_pvd)
    target_trk_bytes = struct.pack('<I', target_fad_trk)
    
    known_fads_pvd = [struct.pack('<I', 45166), struct.pack('<I', 11868)]
    known_fads_trk = [struct.pack('<I', 45150), struct.pack('<I', 11852)]
    
    total_patched = 0
    target_exts = ('1ST_READ.BIN', 'SG_DPLDR.BIN', 'MAIGO.BIN', '2_DP.BIN', 'EST1ST.BIN', 'EPF1ST.BIN')

    for root, dirs, files in os.walk(staging_dir):
        for f in files:
            if f.upper() in target_exts:
                fpath = os.path.join(root, f)
                with open(fpath, 'rb') as fp:
                    data = bytearray(fp.read())
                
                modified = False
                
                # Caso especial quirúrgico: Marvel vs. Capcom 2 (1ST_READ.BIN de 1,811,728 bytes)
                if len(data) == 1811728:
                    if data[0x1660b0:0x1660b4] != target_trk_bytes:
                        data[0x1660b0:0x1660b4] = target_trk_bytes
                        modified = True
                    if data[0x16647c:0x166480] != target_trk_bytes:
                        data[0x16647c:0x166480] = target_trk_bytes
                        modified = True
                    if data[0x1b4310:0x1b4314] != target_pvd_bytes:
                        data[0x1b4310:0x1b4314] = target_pvd_bytes
                        modified = True

                for old_pvd in known_fads_pvd:
                    if old_pvd != target_pvd_bytes:
                        idx = 0
                        while True:
                            pos = data.find(old_pvd, idx)
                            if pos < 0: break
                            data[pos:pos+4] = target_pvd_bytes
                            modified = True
                            idx = pos + 4
                            
                for old_trk in known_fads_trk:
                    if old_trk != target_trk_bytes:
                        idx = 0
                        while True:
                            pos = data.find(old_trk, idx)
                            if pos < 0: break
                            data[pos:pos+4] = target_trk_bytes
                            modified = True
                            idx = pos + 4
                
                if modified:
                    # Romper hardlink para no alterar el archivo fuente en Games/
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass
                    with open(fpath, 'wb') as fp:
                        fp.write(data)
                    total_patched += 1
                    if verbose:
                        rel = os.path.relpath(fpath, staging_dir)
                        print(f"  [✓] Binario calibrado a LBA {target_lba} (PVD FAD {target_fad_pvd}): {rel}")

    # Calibrar TOC y cabecera de IP.BIN para MIL-CD
    ip_bin_path = os.path.join(staging_dir, 'IP.BIN')
    if os.path.isfile(ip_bin_path):
        with open(ip_bin_path, 'rb') as fp:
            ip_data = bytearray(fp.read())
            
        # 1. Configurar tipo de medio a CD-ROM1/1
        if target_lba == 11702:
            ip_data[0x20:0x30] = b'    CD-ROM1/1   '
        else:
            ip_data[0x20:0x30] = b'    GD-ROM1/1   '
            
        # 2. Calibrar TOC1 (Slot 1 a Track FAD con flag 0x41 y limpiar tracks fantasma a 0xFF)
        ip_data[0x100:0x104] = b'TOC1'
        ip_data[0x104:0x107] = struct.pack('<I', target_fad_trk)[:3]
        ip_data[0x107] = 0x41
        ip_data[0x108:0x160] = b'\xff' * (0x160 - 0x108)
        
        try:
            os.remove(ip_bin_path)
        except OSError:
            pass
        with open(ip_bin_path, 'wb') as fp:
            fp.write(ip_data)
        if verbose:
            print(f"  [✓] IP.BIN TOC calibrado a LBA {target_lba} (Track FAD {target_fad_trk}, CD-ROM Mode)")

    return total_patched

