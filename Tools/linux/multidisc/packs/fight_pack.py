#!/usr/bin/env python3
"""
fight_pack.py - Orquestador para la compilación del Capcom Fight Pack (3-en-1 para CD-R 700MB).
"""

import os
import shutil
from .base import prepare_frontend_base, stage_game_files, REPO_ROOT, GAMES_DIR, FRONTEND_DEFAULT_DIR
from ..staging.deduplicator import deduplicate_staging_directory
from ..staging.inspector import run_preflight_inspection
from ..core.cdi_container import build_multidisc_cdi

def build_capcom_fight_pack_cdi(output_cdi_path: str, volume_name: str = "CAPCOM_FIGHT_PACK", custom_template_html: str = None, verbose: bool = True):
    """
    Construye la compilación multijuego Capcom Fight Pack 3-en-1 calibrada para CD-R 700MB:
    - 1. Marvel vs Capcom 2: Nene Edition (/GAME20)
    - 2. Capcom vs SNK 2: English v1.2 (/JAPCVS) desde dump nativo GDI
    - 3. Super Street Fighter II X: Grand Master Challenge (/ST)
    """
    # 0. Diagnóstico y sugerencias pre-armado
    if verbose:
        games_cfg = {
            'GAME20': {'name': 'Marvel vs Capcom 2 (Nene Edition)', 'path': os.path.join(REPO_ROOT, 'MVC2')},
            'JAPCVS': {'name': 'Capcom vs SNK 2 (English v1.2)', 'path': os.path.join(GAMES_DIR, 'CVS2')},
            'ST': {'name': 'Super Street Fighter II X (ST)', 'path': os.path.join(GAMES_DIR, 'SSF2X')},
        }
        run_preflight_inspection(games_cfg, verbose=verbose)

    staging_dir = os.path.join(os.path.dirname(os.path.abspath(output_cdi_path)), "_staging_capcom_fightpack")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    if verbose:
        print("========================================================================")
        print("   Capcom Fight Pack 3-en-1 (CD-R 700MB): MvC2 Nene + CvS2 English + ST")
        print("========================================================================")
        print(f"[*] Directorio de Módulos: {GAMES_DIR}")
        print(f"[*] CDI Destino          : {output_cdi_path}")

    # 1. Preparar Frontend Base y Menú HTML
    template_path = custom_template_html
    if not template_path:
        default_tpl = os.path.join(FRONTEND_DEFAULT_DIR, "DPWWW", "templates", "fightpack_3in1.html")
        if os.path.exists(default_tpl):
            template_path = default_tpl

    prepare_frontend_base(staging_dir, template_html_path=template_path)

    # 2. Agregar los 3 juegos
    print("[*] Enlazando juegos a staging...")
    vanilla_1st_read = os.path.join(GAMES_DIR, "MVC2_Vanilla", "1ST_READ.BIN")
    # GAME20: MvC2 Nene Edition
    stage_game_files(os.path.join(REPO_ROOT, "MVC2"), os.path.join(staging_dir, "GAME20"), custom_1st_read=vanilla_1st_read)
    # JAPCVS: CvS2 English v1.2 (GDI Nativo)
    stage_game_files(os.path.join(GAMES_DIR, "CVS2"), os.path.join(staging_dir, "JAPCVS"))
    # ST: SSF2X Super Turbo
    stage_game_files(os.path.join(GAMES_DIR, "SSF2X"), os.path.join(staging_dir, "ST"))

    # 3. De-duplicación global de assets
    deduplicate_staging_directory(staging_dir, verbose=verbose)

    # 4. Compilar CDI autobootable
    res = build_multidisc_cdi(staging_dir, output_cdi_path, volume_name=volume_name, verbose=verbose)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return res
