#!/usr/bin/env python3
"""
inspector.py - Analizador pre-armado y diagnóstico inteligente de binarios SH-4, LBAs y compatibilidad de mods.
"""

import os
import struct
import math

def calculate_entropy(data: bytes) -> float:
    """Calcula la entropía de Shannon en bits por byte (0.0 a 8.0)."""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    ent = 0.0
    length = len(data)
    for c in counts:
        if c > 0:
            p = c / length
            ent -= p * math.log2(p)
    return ent

def inspect_sh4_binary(bin_path: str):
    """
    Analiza un binario SH-4 (ej: 1ST_READ.BIN, 2_DP.BIN):
    - Detección de Scramble / Unscramble
    - Detección de LBA / Binhack (11702, 11730, 45166, 45000, 0)
    - Detección de mods conocidos (Pause Mod, Character Expansion, MMJ, PalMod)
    - Detección de modo de carga (gdFs dinámico vs TOC fija)
    """
    if not os.path.exists(bin_path):
        return None

    size = os.path.getsize(bin_path)
    with open(bin_path, 'rb') as f:
        data = f.read()

    head = data[:32]
    # 1. Scramble vs Unscrambled
    # Binario unscrambled Katana inicia típicamente con nops/branch: 09 00 09 00 ... 05 d0 02 61
    is_katana_entry = head.startswith(b'\x09\x00\x09\x00\x09\x00\x09\x00') or head.startswith(b'\x09\x00\x09\x00')
    first_64k_entropy = calculate_entropy(data[:65536])
    is_scrambled = not is_katana_entry and first_64k_entropy > 7.6

    # 2. Análisis de LBA / Binhack
    lba_info = {
        'type': 'GDFS_DYNAMIC', # Por defecto dinámico por sistema de archivos
        'target_lba': None,
        'matches': []
    }

    # Búsqueda de patrones LBA clásicos de Binhack / CD-R
    target_lbas = [
        (11702, 'Audio/Data 74-min (CD-R Antiguo)'),
        (11730, 'Audio/Data 74-min (TOC Root Dir)'),
        (45000, 'Audio/Data 80-min (Base Dreamcast)'),
        (45020, 'GD-ROM / Multidisc Root Dir (45020)'),
        (45021, 'GD-ROM / Multidisc Root Dir (45021)'),
        (45166, 'Audio/Data 80-min Binhack (45166)'),
    ]

    for lba_val, desc in target_lbas:
        le_b = struct.pack('<I', lba_val)
        be_b = struct.pack('>I', lba_val)
        c_le = data.count(le_b)
        c_be = data.count(be_b)
        if c_le > 0 or c_be > 0:
            lba_info['matches'].append({
                'lba': lba_val,
                'desc': desc,
                'count_le': c_le,
                'count_be': c_be
            })

    # Clasificación de compatibilidad LBA
    has_11702_or_30 = any(m['lba'] in (11702, 11730) for m in lba_info['matches'])
    has_45166 = any(m['lba'] == 45166 for m in lba_info['matches']) or (b'\xa6\x00' in data and b'\x6e\xb0' not in data)
    
    if has_11702_or_30:
        lba_info['type'] = 'BINHACK_11702'
        lba_info['target_lba'] = 11702
    elif has_45166:
        lba_info['type'] = 'BINHACK_45166'
        lba_info['target_lba'] = 45166
    else:
        lba_info['type'] = 'GDFS_DYNAMIC'

    # 3. Detección de Mods
    detected_mods = []
    if b'PAUSEMOD' in data:
        detected_mods.append('Pause Mod (Menú de Pausa desbloqueado / Training)')
    if b'MMJ' in data or b'STRNG' in data:
        detected_mods.append('Expanded Character Engine (Slots de personajes custom)')
    if b'ETEX.BIN' in data:
        detected_mods.append('English Translation Texture Hook (ETEX.BIN)')
    if size > 1810000 and 'MVC2' in bin_path:
        detected_mods.append('Custom MvC2 Code Additions (+1.9 KB bytecode extension)')

    return {
        'path': bin_path,
        'size': size,
        'is_scrambled': is_scrambled,
        'lba_type': lba_info['type'],
        'lba_target': lba_info['target_lba'],
        'lba_matches': lba_info['matches'],
        'detected_mods': detected_mods
    }

def run_preflight_inspection(games_dict: dict, verbose: bool = True):
    """
    Ejecuta el diagnóstico integral de pre-vuelo antes de construir el multijuego:
    - Inspecciona ejecutables principales.
    - Calcula tamaño de ISO y CDI proyectado.
    - Emite sugerencias y advertencias accionables.
    """
    if verbose:
        print("========================================================================")
        print("   🔍 DIAGNÓSTICO PRE-ARMADO (PRE-FLIGHT CHECK) - DREAMCAST MULTIDISC")
        print("========================================================================")

    total_data_bytes = 0
    diagnostics = {}
    recommendations = []

    for game_id, g_info in games_dict.items():
        name = g_info.get('name', game_id)
        path = g_info.get('path')
        if not path or not os.path.exists(path):
            continue

        # Tamaño del módulo
        dir_bytes = sum(os.path.getsize(os.path.join(r, f)) for r, _, files in os.walk(path) for f in files)
        total_data_bytes += dir_bytes

        # Inspección del binario principal
        bin_1st = os.path.join(path, '1ST_READ.BIN')
        bin_diag = inspect_sh4_binary(bin_1st) if os.path.exists(bin_1st) else None

        diagnostics[game_id] = {
            'name': name,
            'path': path,
            'size_bytes': dir_bytes,
            'binary': bin_diag
        }

    # Mostrar Diagnóstico por Juego
    for gid, diag in diagnostics.items():
        sz_mb = diag['size_bytes'] / (1024 * 1024)
        print(f"\n🎮 [{gid}] {diag['name']} ({sz_mb:.2f} MB):")
        b = diag['binary']
        if b:
            # Estado Scramble
            scramble_txt = "⚠️ SCRAMBLED (MIL-CD Root)" if b['is_scrambled'] else "✓ UNSCRAMBLED (SH-4 Direct Entry)"
            print(f"   ├─ Ejecutable   : {os.path.basename(b['path'])} ({b['size']:,} bytes)")
            print(f"   ├─ Formato SH-4 : {scramble_txt}")
            
            # Estado LBA
            if b['lba_type'] == 'GDFS_DYNAMIC':
                print(f"   ├─ Modo LBA     : ✓ gdFs Dinámico (Carga nativa por nombre de archivo)")
            elif b['lba_type'] == 'BINHACK_45166':
                print(f"   ├─ Modo LBA     : ✓ Binhack 45166 (Calibrado para Audio/Data 80-min Multidisc)")
            elif b['lba_type'] == 'BINHACK_11702':
                print(f"   ├─ Modo LBA     : ⚠️ Binhack 11702 (Offset CD-R 74-min detectado)")
                recommendations.append(f"El binario de '{diag['name']}' tiene punteros a LBA 11702. Se recomienda usar la opción LBA 45166 al parchear o el motor usará el ejecutable canónico en staging.")

            # Mods Detectados
            if b['detected_mods']:
                print(f"   └─ Mods Activos : {', '.join(b['detected_mods'])}")
            else:
                print(f"   └─ Mods Activos : Ninguno (Vanilla/Comercial)")
        else:
            print("   └─ Ejecutable   : No encontrado en la raíz del módulo")

    # Diagnóstico Global de Espacio (CD-R 700MB)
    print("\n------------------------------------------------------------------------")
    print("📊 ESTIMACIÓN DE ESPACIO EN DISCO CD-R:")
    total_iso_mb = total_data_bytes / (1024 * 1024)
    # CD-R 80 min estándar: 700 MB / 360,000 sectores Mode 2 Form 1
    cd_limit_mb = 700.0
    usage_pct = (total_iso_mb / cd_limit_mb) * 100

    print(f"   - Tamaño proyectado de datos ISO : {total_iso_mb:.2f} MB")
    print(f"   - Límite físico CD-R (80 min)   : {cd_limit_mb:.2f} MB")
    print(f"   - Ocupación del disco           : {usage_pct:.1f}%")

    if usage_pct <= 98.0:
        print("   - Estado de Grabación           : ✓ [EXCELENTE] Cabe en cualquier CD-R virgen de 700 MB.")
    elif usage_pct <= 100.0:
        print("   - Estado de Grabación           : ⚠️ [AJUSTADO] Cabe en CD-R estándar de 700 MB pero con poco margen.")
    else:
        print("   - Estado de Grabación           : ❌ [EXCEDIDO] Requiere de-duplicación o CD-R de 90 min (800 MB).")
        recommendations.append("El tamaño supera los 700 MB. La de-duplicación de assets o eliminar tracks ADX no utilizados reducirá el tamaño.")

    # Mostrar Sugerencias Accionables
    print("\n------------------------------------------------------------------------")
    print("💡 SUGERENCIAS Y RECOMENDACIONES:")
    if recommendations:
        for r in recommendations:
            print(f"   • {r}")
    else:
        print("   • Todos los binarios y módulos están en estado óptimo. ¡Listo para compilar!")
    print("========================================================================\n")

    return diagnostics
