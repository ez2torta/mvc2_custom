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

    # 6. build-holamundo
    p_hola = subparsers.add_parser('build-holamundo', help='Mini-mini-experimento: Solo Browser Hola Mundo (CDI)')
    p_hola.add_argument('--output', '-o', default=None, help='Ruta del archivo .cdi de salida')
    p_hola.add_argument('--volume', '-v', default='HOLA_MUNDO', help='Nombre de volumen ISO')

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
        build_capcom_fight_pack_cdi(out_cdi, volume_name=args.volume, custom_template_html=args.template)
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
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

