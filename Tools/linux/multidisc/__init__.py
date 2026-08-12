"""
Multidisc Engine for Sega Dreamcast (Modular Architecture)
"""

from .core.iso9660 import build_iso9660_with_deduplication
from .core.cdi_container import package_audio_data_cdi, build_multidisc_cdi
from .core.edc_ecc import get_libedc
from .staging.deduplicator import deduplicate_staging_directory
from .staging.extractor import extract_cdi_track2, extract_gdi
from .packs.fight_pack import build_capcom_fight_pack_cdi
from .packs.tests import build_mini_puzzle_cdi, build_mini_puzzle_gdi, build_hola_mundo_cdi
from .packs.base import prepare_frontend_base, stage_game_files

__all__ = [
    'build_iso9660_with_deduplication',
    'package_audio_data_cdi',
    'build_multidisc_cdi',
    'get_libedc',
    'deduplicate_staging_directory',
    'extract_cdi_track2',
    'extract_gdi',
    'build_capcom_fight_pack_cdi',
    'build_mini_puzzle_cdi',
    'build_mini_puzzle_gdi',
    'build_hola_mundo_cdi',
    'prepare_frontend_base',
    'stage_game_files'
]
