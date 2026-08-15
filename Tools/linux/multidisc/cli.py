#!/usr/bin/env python3
"""
cli.py - Interfaz de línea de comandos unificada para el motor multidisco de Dreamcast.
"""

import os
import argparse
from .core.cdi_container import build_multidisc_cdi
from .staging.extractor import extract_cdi_track2, extract_gdi
from .packs.fight_pack import build_capcom_fight_pack_cdi
from .packs.tests import build_mini_puzzle_cdi, build_mini_puzzle_gdi, build_hola_mundo_cdi, build_mini_cvs1j_cdi
from .packs.base import REPO_ROOT

def main():
    parser = argparse.ArgumentParser(description='Gestor de compilaciones Multijuego y Multi-Soundtrack para Dreamcast')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')

    # 1. extract (CDI)
    p_extract = subparsers.add_parser('extract', help='Extrae un CDI multijuego preservando hardlinks')
    p_extract.add_argument('--input', '-i', required=True, help='Ruta al archivo .cdi origen (ej: TDCFinal2/disc.cdi)')
    p_extract.add_argument('--output', '-o', required=True, help='Directorio de salida para los juegos extraídos')

    # 1.1 extract-gdi (GDI nativo GD-ROM)
    p_extract_gdi = subparsers.add_parser('extract-gdi', help='Extrae todos los archivos de un volcado GDI de Dreamcast (LBA 45000)')
    p_extract_gdi.add_argument('--input', '-i', required=True, help='Ruta al archivo disc.gdi o carpeta que lo contiene')
    p_extract_gdi.add_argument('--output', '-o', required=True, help='Directorio de salida para los archivos extraídos')

    # 1.2 inspect (diagnóstico pre-armado)
    p_insp = subparsers.add_parser('inspect', help='Ejecuta diagnóstico pre-armado y sugerencias de compatibilidad de binarios')
    p_insp.add_argument('--path', '-p', default=None, help='Ruta a un binario SH-4 específico o directorio de juego')

    # 2. build (desde carpeta arbitraria)
    p_build = subparsers.add_parser('build', help='Construye un CDI multijuego desde estructura existente con de-duplicación')
    p_build.add_argument('--input', '-i', required=True, help='Directorio con la estructura de juegos y hardlinks')
    p_build.add_argument('--output', '-o', required=True, help='Ruta del archivo .cdi de salida')
    p_build.add_argument('--volume', '-v', default='MULTIDISC', help='Nombre de volumen ISO')

    # 3. build-modular / build-fightpack / build-4pack
    for cmd_name in ['build-modular', 'build-fightpack', 'build-4pack']:
        p_mod = subparsers.add_parser(cmd_name, help='Compila el Capcom Fight Pack (MvC2 Nene + CvS2 English + Super Turbo)')
        p_mod.add_argument('--output', '-o', default=None, help='Ruta del archivo .cdi de salida')
        p_mod.add_argument('--template', '-t', default=None, help='Ruta a plantilla HTML personalizada (opcional)')
        p_mod.add_argument('--volume', '-v', default='CAPCOM_FIGHT_PACK', help='Nombre de volumen ISO')
        p_mod.add_argument('--lba', type=int, default=11702, help='Base LBA para la pista de datos (default: 11702)')

    # 4. build-mini
    p_mini = subparsers.add_parser('build-mini', help='Mini-experimento: Menú + Super Puzzle Fighter II X (CDI)')
    p_mini.add_argument('--output', '-o', default=None, help='Ruta del archivo .cdi de salida')
    p_mini.add_argument('--volume', '-v', default='PUZZLE_FIGHTER', help='Nombre de volumen ISO')

    # 4.1 build-mini-cvs
    p_mini_cvs = subparsers.add_parser('build-mini-cvs', help='Mini-experimento: Menú Dricas + Capcom vs. SNK Japan (LBA 45000 CDI)')
    p_mini_cvs.add_argument('--output', '-o', default=None, help='Ruta del archivo .cdi de salida')
    p_mini_cvs.add_argument('--volume', '-v', default='CAPCOM_VS_SNK', help='Nombre de volumen ISO')

    # 5. build-mini-gdi
    p_mini_gdi = subparsers.add_parser('build-mini-gdi', help='Mini-experimento: Menú + Super Puzzle Fighter II X (GDI)')
    p_mini_gdi.add_argument('--output', '-o', default=None, help='Directorio de salida GDI')
    p_mini_gdi.add_argument('--volume', '-v', default='PUZZLE_FIGHTER', help='Nombre de volumen ISO')

    # 7. adx-downsample
    p_adx = subparsers.add_parser('adx-downsample', help='Optimiza y downsamplea pistas CRI ADX a 22kHz mono recalculando loop points')
    p_adx.add_argument('input', help='Archivo o carpeta con pistas ADX')
    p_adx.add_argument('output', nargs='?', default=None, help='Archivo o carpeta destino')
    p_adx.add_argument('--rate', type=int, default=22050, help='Frecuencia objetivo en Hz (default: 22050)')
    p_adx.add_argument('--channels', type=int, default=1, help='Canales (1=Mono, 2=Stereo, default: 1)')
    p_adx.add_argument('--no-normalize', action='store_true', help='Desactiva normalización EBU R128')
    p_adx.add_argument('--in-place', action='store_true', help='Sobrescribe archivos en su lugar')
    p_adx.add_argument('--no-backup', action='store_true', help='No genera copias .orig_bak')

    # 8. soundtrack-matrix / soundtrack-list
    p_st_list = subparsers.add_parser('soundtrack-matrix', help='Muestra la tabla de combinaciones cruzadas de bandas sonoras')
    p_st_list.add_argument('--game', default=None, help='Filtrar por juego objetivo (MVC2, CVS2, SSF2X, 3S, PF)')

    # 9. soundtrack-mix
    p_st_mix = subparsers.add_parser('soundtrack-mix', help='Genera una variante de juego con banda sonora personalizada')
    p_st_mix.add_argument('--game', required=True, help='Juego objetivo (MVC2, CVS2, SSF2X, 3S, PF)')
    p_st_mix.add_argument('--soundtrack', required=True, help='Banda sonora elegida (3S, CVS2, ST, PF, MVC2, FANDISK, SILENT)')
    p_st_mix.add_argument('--base-dir', required=True, help='Directorio del juego base')
    p_st_mix.add_argument('--out-dir', required=True, help='Directorio destino para la variante')
    p_st_mix.add_argument('--adx-pool', default=None, help='Directorio con los archivos ADX fuente')

    # 10. soundtrack-generate
    p_st_gen = subparsers.add_parser('soundtrack-generate', help='Genera todas las variantes de bandas sonoras de un juego para staging')
    p_st_gen.add_argument('--game', required=True, help='Juego objetivo (MVC2, CVS2, SSF2X, 3S, PF)')
    p_st_gen.add_argument('--base-dir', required=True, help='Directorio del juego base')
    p_st_gen.add_argument('--staging-dir', required=True, help='Directorio staging donde colocar GAME20, GAME24, etc.')
    p_st_gen.add_argument('--adx-pool', default=None, help='Directorio con los archivos ADX fuente')

    args = parser.parse_args()

    if args.command == 'extract':
        extract_cdi_track2(args.input, args.output)
    elif args.command == 'extract-gdi':
        extract_gdi(args.input, args.output)
    elif args.command == 'inspect':
        from .staging.inspector import run_preflight_inspection, inspect_sh4_binary
        if args.path and os.path.isfile(args.path):
            diag = inspect_sh4_binary(args.path)
            print(f"[*] Inspección de binario individual: {args.path}")
            for k, v in diag.items():
                print(f"  {k:15s}: {v}")
        else:
            from .packs.base import GAMES_DIR
            games_cfg = {
                'GAME20': {'name': 'Marvel vs Capcom 2 (Nene Edition)', 'path': os.path.join(REPO_ROOT, 'MVC2')},
                'JAPCVS': {'name': 'Capcom vs SNK 2 (English v1.2)', 'path': os.path.join(GAMES_DIR, 'CVS2')},
                'ST': {'name': 'Super Street Fighter II X (ST)', 'path': os.path.join(GAMES_DIR, 'SSF2X')},
            }
            if args.path and os.path.isdir(args.path):
                games_cfg = {'CUSTOM': {'name': os.path.basename(args.path), 'path': args.path}}
            run_preflight_inspection(games_cfg)
    elif args.command == 'build':
        build_multidisc_cdi(args.input, args.output, volume_name=args.volume)
    elif args.command in ('build-modular', 'build-fightpack', 'build-4pack'):
        out_cdi = args.output if args.output else os.path.join(REPO_ROOT, 'output_cdi', 'capcom_fight_pack.cdi')
        build_capcom_fight_pack_cdi(out_cdi, volume_name=args.volume, custom_template_html=args.template, base_lba=args.lba)
    elif args.command == 'build-mini':
        out_cdi = args.output if args.output else os.path.join(REPO_ROOT, 'output_cdi', 'mini_puzzle_multidisc.cdi')
        build_mini_puzzle_cdi(out_cdi, volume_name=args.volume)
    elif args.command == 'build-mini-cvs':
        out_cdi = args.output if args.output else os.path.join(REPO_ROOT, 'output_cdi', 'mini_cvs1j_multidisc.cdi')
        build_mini_cvs1j_cdi(out_cdi, volume_name=args.volume)
    elif args.command == 'build-mini-gdi':
        out_gdi = args.output if args.output else os.path.join(REPO_ROOT, 'output_gdi_mini_puzzle')
        build_mini_puzzle_gdi(out_gdi, volume_name=args.volume)
    elif args.command == 'build-holamundo':
        out_cdi = args.output if args.output else os.path.join(REPO_ROOT, 'output_cdi', 'hola_mundo_dreamcast.cdi')
        build_hola_mundo_cdi(out_cdi, volume_name=args.volume)
    elif args.command == 'adx-downsample':
        import adx_downsampler
        if os.path.isfile(args.input):
            out_f = args.output or args.input
            adx_downsampler.downsample_adx_file(args.input, out_f, target_rate=args.rate, target_channels=args.channels, normalize=not args.no_normalize, verbose=True)
        elif os.path.isdir(args.input):
            adx_downsampler.batch_downsample_directory(args.input, output_dir=args.output, target_rate=args.rate, target_channels=args.channels, normalize=not args.no_normalize, in_place=args.in_place, backup=not args.no_backup, verbose=True)
    elif args.command == 'soundtrack-matrix':
        import soundtrack_manager
        soundtrack_manager.print_soundtrack_matrix_table(args.game)
    elif args.command == 'soundtrack-mix':
        import soundtrack_manager
        adx_pool = args.adx_pool or soundtrack_manager.ADXFILES_DIR
        soundtrack_manager.generate_mixed_game_directory(base_game_dir=args.base_dir, output_game_dir=args.out_dir, target_game_key=args.game, soundtrack_key=args.soundtrack, adx_pool_dir=adx_pool, verbose=True)
    elif args.command == 'soundtrack-generate':
        import soundtrack_manager
        adx_pool = args.adx_pool or soundtrack_manager.ADXFILES_DIR
        soundtrack_manager.generate_all_soundtrack_variants_for_game(target_game_key=args.game, base_game_dir=args.base_dir, staging_dir=args.staging_dir, adx_pool_dir=adx_pool, verbose=True)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

