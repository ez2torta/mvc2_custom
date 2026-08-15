#!/usr/bin/env python3
"""
json_pack.py - Orquestador declarativo basado en JSON para compilar cualquier multijuego de Sega Dreamcast.
"""

import os
import sys
import json
import shutil
from typing import Dict, Any, List

from .base import (
    prepare_frontend_base,
    stage_game_files,
    REPO_ROOT,
    GAMES_DIR,
    FRONTEND_DEFAULT_DIR,
    MULTIDISC_ROOT,
    retarget_staged_binaries_for_lba
)
from ..staging.deduplicator import deduplicate_staging_directory
from ..staging.inspector import run_preflight_inspection
from ..core.cdi_container import build_multidisc_cdi

def resolve_path(p: str, base_dir: str = REPO_ROOT) -> str:
    if not p:
        return ""
    if os.path.isabs(p):
        return p
    # First check relative to REPO_ROOT, then base_dir
    cand1 = os.path.abspath(os.path.join(REPO_ROOT, p))
    if os.path.exists(cand1):
        return cand1
    cand2 = os.path.abspath(os.path.join(base_dir, p))
    if os.path.exists(cand2):
        return cand2
    return cand1

def build_multidisc_from_json(config_path_or_dict, output_override: str = None, verbose: bool = True):
    """
    Lee un archivo JSON descriptivo de multijuego y construye la imagen CDI automáticamente.
    """
    if isinstance(config_path_or_dict, str):
        config_path = resolve_path(config_path_or_dict)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"No se encontró el archivo de configuración JSON: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        config_dir = os.path.dirname(config_path)
    else:
        cfg = config_path_or_dict
        config_dir = REPO_ROOT

    volume_name = cfg.get("volume_name", "MULTIDISC_DC")
    base_lba = cfg.get("base_lba", 11702)
    output_cdi = output_override if output_override else cfg.get("output_cdi", "output_cdi/multidisc_custom.cdi")
    output_cdi_path = resolve_path(output_cdi)

    # 1. Preparar diagnóstico de juegos definidos
    games_list: List[Dict[str, Any]] = cfg.get("games", [])
    if not games_list:
        raise ValueError("El archivo JSON debe contener al menos un juego en la lista 'games'.")

    if verbose:
        print("========================================================================")
        print(f"   COMPILADOR MULTIJUEGO DREAMCAST DECLARATIVO (JSON ENGINE)")
        print("========================================================================")
        print(f"[*] Volumen ISO  : {volume_name}")
        print(f"[*] Base LBA     : {base_lba}")
        print(f"[*] CDI Salida   : {output_cdi_path}")
        print(f"[*] Total Juegos : {len(games_list)}")
        print("------------------------------------------------------------------------")

    # Staging dir
    staging_dir = os.path.join(os.path.dirname(output_cdi_path), f"_staging_{volume_name.lower()}")
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    # 2. Preparar Frontend Base y Template HTML
    template_html = cfg.get("menu_template")
    template_path = resolve_path(template_html) if template_html else None
    prepare_frontend_base(staging_dir, template_html_path=template_path)

    # 3. Importar gestor de soundtracks
    if MULTIDISC_ROOT not in sys.path:
        sys.path.insert(0, MULTIDISC_ROOT)
    import soundtrack_manager

    adx_pool_default = os.path.join(staging_dir, "ADXFILES") if os.path.isdir(os.path.join(staging_dir, "ADXFILES")) else soundtrack_manager.ADXFILES_DIR

    # 4. Procesar cada juego en la lista
    for g in games_list:
        gid = g.get("id")
        gname = g.get("name", gid)
        gsrc = resolve_path(g.get("source_dir", ""), config_dir)
        custom_read = resolve_path(g["custom_1st_read"], config_dir) if "custom_1st_read" in g else None

        if not os.path.isdir(gsrc):
            print(f"[!] ADVERTENCIA: Directorio de juego no encontrado para '{gname}': {gsrc}")
            continue

        target_game_dir = os.path.join(staging_dir, gid)
        if verbose:
            print(f"[*] Enlazando módulo '{gname}' -> /{gid}")
        stage_game_files(gsrc, target_game_dir, custom_1st_read=custom_read)

        # Inyectar pool de audios custom si se especificó
        if "audio_pool" in g:
            apool = resolve_path(g["audio_pool"], config_dir)
            if os.path.isdir(apool):
                for af in os.listdir(apool):
                    if af.endswith(".BIN") or af.endswith(".ADX"):
                        s_adx = os.path.join(apool, af)
                        d_adx = os.path.join(target_game_dir, af)
                        if os.path.exists(d_adx):
                            os.remove(d_adx)
                        shutil.copy2(s_adx, d_adx)

        # Generar variantes de soundtrack si se especificaron
        st_variants = g.get("generate_soundtracks", [])
        if st_variants:
            target_key = g.get("soundtrack_target_key", gid.upper())
            # Normalizar key
            if "MVC" in target_key: target_key = "MVC2"
            elif "CVS2" in target_key: target_key = "CVS2"
            elif "CVS" in target_key or "CVS1" in target_key: target_key = "CVS1"
            elif "ST" in target_key or "SSF2" in target_key: target_key = "ST"
            elif "3S" in target_key: target_key = "3S"
            elif "PF" in target_key: target_key = "PF"

            if verbose:
                print(f"    -> Generando variantes de soundtrack {st_variants} para {gid}...")
            
            if "ALL" in st_variants:
                soundtrack_manager.generate_all_soundtrack_variants_for_game(
                    target_game_key=target_key,
                    base_game_dir=target_game_dir,
                    staging_dir=staging_dir,
                    adx_pool_dir=adx_pool_default,
                    verbose=False
                )
            else:
                for svar in st_variants:
                    if svar == "SILENT":
                        dir_info = soundtrack_manager.STANDARD_LAUNCHER_MATRIX.get(target_key, {}).get("SILENT", (f"GAME_{gid}_SILENT", 0, "Silent"))
                        soundtrack_manager.generate_mixed_game_directory(
                            base_game_dir=target_game_dir,
                            output_game_dir=os.path.join(staging_dir, dir_info[0]),
                            target_game_key=target_key,
                            soundtrack_key="SILENT",
                            matrix=None,
                            adx_pool_dir=adx_pool_default,
                            verbose=False
                        )
                    else:
                        dir_info = soundtrack_manager.STANDARD_LAUNCHER_MATRIX.get(target_key, {}).get(svar)
                        if dir_info:
                            soundtrack_manager.generate_mixed_game_directory(
                                base_game_dir=target_game_dir,
                                output_game_dir=os.path.join(staging_dir, dir_info[0]),
                                target_game_key=target_key,
                                soundtrack_key=svar,
                                matrix=None,
                                adx_pool_dir=adx_pool_default,
                                verbose=False
                            )

    # 5. Calibrar binarios SH-4 e IP.BIN para el LBA configurado
    if verbose:
        print(f"[*] Calibrando ejecutables SH-4 e IP.BIN para LBA {base_lba}...")
    retarget_staged_binaries_for_lba(staging_dir, target_lba=base_lba, verbose=verbose)

    # 6. De-duplicación global de assets
    deduplicate_staging_directory(staging_dir, verbose=verbose)

    # 7. Compilar CDI autobootable
    res = build_multidisc_cdi(staging_dir, output_cdi_path, volume_name=volume_name, base_lba=base_lba, verbose=verbose)
    shutil.rmtree(staging_dir, ignore_errors=True)
    return res
