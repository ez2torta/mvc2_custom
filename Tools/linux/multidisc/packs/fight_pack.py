#!/usr/bin/env python3
"""
fight_pack.py - Orquestador para la compilación del Capcom Fight Pack (3-en-1 para CD-R 700MB).
"""

import os
import shutil
from .base import prepare_frontend_base, stage_game_files, REPO_ROOT, GAMES_DIR, FRONTEND_DEFAULT_DIR, MULTIDISC_ROOT, retarget_staged_binaries_for_lba
from ..staging.deduplicator import deduplicate_staging_directory
from ..staging.inspector import run_preflight_inspection
from ..core.cdi_container import build_multidisc_cdi

def build_capcom_fight_pack_cdi(output_cdi_path: str, volume_name: str = "CAPCOM_FIGHT_PACK", custom_template_html: str = None, base_lba: int = 11702, verbose: bool = True):
    """
    Construye la compilación multijuego Capcom Fight Pack 4-en-1 calibrada para LBA 11702 (MIL-CD estándar):
    - 1. Marvel vs Capcom 2: Nene Edition (/GAME20) + Vanilla (/USAMVC)
    - 2. Capcom vs SNK 2: English v1.2 (/JAPCVS) + Bonus Mode
    - 3. Capcom vs SNK 1: Millennium Fight 2000 (/CVS1J)
    - 4. Super Street Fighter II X: Grand Master Challenge (/ST)
    """
    # 0. Diagnóstico y sugerencias pre-armado
    if verbose:
        games_cfg = {
            'GAME20': {'name': 'Marvel vs Capcom 2 (Nene Edition)', 'path': os.path.join(REPO_ROOT, 'MVC2')},
            'JAPCVS': {'name': 'Capcom vs SNK 2 (English v1.2)', 'path': os.path.join(GAMES_DIR, 'CVS2')},
            'CVS1J':  {'name': 'Capcom vs SNK (Millennium Fight 2000)', 'path': os.path.join(GAMES_DIR, 'CVS1J') if os.path.isdir(os.path.join(GAMES_DIR, 'CVS1J')) else os.path.join(GAMES_DIR, 'CVS1J_UNLOCK')},
            'ST':     {'name': 'Super Street Fighter II X (ST)', 'path': os.path.join(GAMES_DIR, 'SSF2X')},
        }
        run_preflight_inspection(games_cfg, verbose=verbose)

    staging_dir = os.path.join(os.path.dirname(os.path.abspath(output_cdi_path)), "_staging_capcom_fightpack")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    if verbose:
        print("========================================================================")
        print(f"   Capcom Fight Pack 4-en-1 (CD-R 700MB - LBA {base_lba}): MvC2 + CvS2 + CvS1 + SSF2X")
        print("========================================================================")
        print(f"[*] Directorio de Módulos: {GAMES_DIR}")
        print(f"[*] CDI Destino          : {output_cdi_path}")

    # 1. Preparar Frontend Base y Menú HTML
    template_path = custom_template_html
    if not template_path:
        default_tpl = os.path.join(FRONTEND_DEFAULT_DIR, "DPWWW", "templates", "fightpack_4in1.html")
        if os.path.exists(default_tpl):
            template_path = default_tpl

    prepare_frontend_base(staging_dir, template_html_path=template_path)

    # 2. Agregar los 4 juegos base y sus variantes de soundtrack
    print("[*] Enlazando juegos a staging...")
    # GAME20: MvC2 Nene Edition (con música Custom y mods activos)
    stage_game_files(os.path.join(REPO_ROOT, "MVC2"), os.path.join(staging_dir, "GAME20"))
    # Inyectar audios custom optimizados a 22kHz mono en GAME20
    mvc_custom_pool = os.path.join(FRONTEND_DEFAULT_DIR, "ADXFILES", "MVC_CUSTOM")
    if os.path.isdir(mvc_custom_pool):
        for f in os.listdir(mvc_custom_pool):
            if f.endswith(".BIN") or f.endswith(".ADX"):
                src_adx = os.path.join(mvc_custom_pool, f)
                dst_adx = os.path.join(staging_dir, "GAME20", f)
                if os.path.exists(dst_adx):
                    os.remove(dst_adx)
                shutil.copy2(src_adx, dst_adx)
    
    # USAMVC: MvC2 Vanilla Edition (con música Jazz original)
    vanilla_mvc2_dir = os.path.join(GAMES_DIR, "MVC2_Vanilla")
    if os.path.isdir(vanilla_mvc2_dir):
        stage_game_files(vanilla_mvc2_dir, os.path.join(staging_dir, "USAMVC"))
    else:
        stage_game_files(os.path.join(REPO_ROOT, "MVC2"), os.path.join(staging_dir, "USAMVC"))
        
    # JAPCVS: CvS2 English v1.2 (GDI Nativo)
    stage_game_files(os.path.join(GAMES_DIR, "CVS2"), os.path.join(staging_dir, "JAPCVS"))
    # Inyectar audios optimizados a 22kHz mono en JAPCVS
    cvs_pool = os.path.join(FRONTEND_DEFAULT_DIR, "ADXFILES", "CVS")
    if os.path.isdir(cvs_pool):
        for f in os.listdir(cvs_pool):
            if f.endswith(".BIN") or f.endswith(".ADX"):
                src_adx = os.path.join(cvs_pool, f)
                dst_adx = os.path.join(staging_dir, "JAPCVS", f)
                if os.path.exists(dst_adx):
                    os.remove(dst_adx)
                shutil.copy2(src_adx, dst_adx)

    # CVS1J: Capcom vs SNK 1 (Millennium Fight 2000 Japan)
    cvs1_src = os.path.join(GAMES_DIR, "CVS1J") if os.path.isdir(os.path.join(GAMES_DIR, "CVS1J")) else os.path.join(GAMES_DIR, "CVS1J_UNLOCK")
    stage_game_files(cvs1_src, os.path.join(staging_dir, "CVS1J"))
    # Inyectar audios optimizados a 22kHz mono en CVS1J
    cvs1_pool = os.path.join(FRONTEND_DEFAULT_DIR, "ADXFILES", "CVS1")
    if os.path.isdir(cvs1_pool):
        for f in os.listdir(cvs1_pool):
            if f.endswith(".BIN") or f.endswith(".ADX"):
                src_adx = os.path.join(cvs1_pool, f)
                dst_adx = os.path.join(staging_dir, "CVS1J", f)
                if os.path.exists(dst_adx):
                    os.remove(dst_adx)
                shutil.copy2(src_adx, dst_adx)

    # ST: SSF2X Super Turbo
    stage_game_files(os.path.join(GAMES_DIR, "SSF2X"), os.path.join(staging_dir, "ST"))

    # 2.1 Generar variantes de soundtrack cruzadas (GAME24, GAME26, GAME27, GAME28, GAME29, GAME25, etc.)
    import sys
    if MULTIDISC_ROOT not in sys.path:
        sys.path.insert(0, MULTIDISC_ROOT)
    import soundtrack_manager
    adx_pool = os.path.join(staging_dir, "ADXFILES") if os.path.isdir(os.path.join(staging_dir, "ADXFILES")) else soundtrack_manager.ADXFILES_DIR
    
    print("[*] Generando variantes de soundtrack cruzadas para Marvel vs Capcom 2...")
    soundtrack_manager.generate_all_soundtrack_variants_for_game(target_game_key="MVC2", base_game_dir=os.path.join(staging_dir, "GAME20"), staging_dir=staging_dir, adx_pool_dir=adx_pool, verbose=False)
    
    # Generar GAME25 (Silent Mode para MvC2)
    soundtrack_manager.generate_mixed_game_directory(base_game_dir=os.path.join(staging_dir, "GAME20"), output_game_dir=os.path.join(staging_dir, "GAME25"), target_game_key="MVC2", soundtrack_key="SILENT", matrix=None, adx_pool_dir=adx_pool, verbose=False)

    print("[*] Generando variantes de soundtrack cruzadas para Capcom vs SNK 1...")
    soundtrack_manager.generate_all_soundtrack_variants_for_game(target_game_key="CVS1", base_game_dir=os.path.join(staging_dir, "CVS1J"), staging_dir=staging_dir, adx_pool_dir=adx_pool, verbose=False)

    print("[*] Generando variantes de soundtrack cruzadas para CvS2 y Super Turbo...")
    soundtrack_manager.generate_all_soundtrack_variants_for_game(target_game_key="CVS2", base_game_dir=os.path.join(staging_dir, "JAPCVS"), staging_dir=staging_dir, adx_pool_dir=adx_pool, verbose=False)
    soundtrack_manager.generate_all_soundtrack_variants_for_game(target_game_key="ST", base_game_dir=os.path.join(staging_dir, "ST"), staging_dir=staging_dir, adx_pool_dir=adx_pool, verbose=False)

    # 2.2 Calibrar dinámicamente todos los ejecutables SH-4 e IP.BIN al LBA objetivo (11702 o 45000)
    print(f"[*] Calibrando ejecutables SH-4 e IP.BIN para LBA {base_lba}...")
    retarget_staged_binaries_for_lba(staging_dir, target_lba=base_lba, verbose=verbose)

    # 3. De-duplicación global de assets (fusiona miles de archivos idénticos a 0 MB adicionales)
    deduplicate_staging_directory(staging_dir, verbose=verbose)

    # 4. Compilar CDI autobootable
    res = build_multidisc_cdi(staging_dir, output_cdi_path, volume_name=volume_name, base_lba=base_lba, verbose=verbose)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return res
