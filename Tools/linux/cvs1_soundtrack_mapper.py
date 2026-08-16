#!/usr/bin/env python3
"""
cvs1_soundtrack_mapper.py - Herramienta interactiva para mapear, audicionar y calibrar
las pistas de audio ADX de Capcom vs SNK 1 (Millennium Fight 2000).

Comandos disponibles:
  - list         : Muestra la tabla completa de todas las pistas de CvS1 y sus mapeos cruzados.
  - export-audio : Exporta todas las pistas de CvS1 a MP3 en Extracted_Audio/CVS1_MP3/ para escucharlas fácilmente.
  - edit         : Exporta / sincroniza el archivo editable Docs/CVS1_SOUNDTRACK_MAP.json
  - apply        : Lee Docs/CVS1_SOUNDTRACK_MAP.json y actualiza el motor de multidisc automáticamente.
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
CVS1_DIR = os.path.join(REPO_ROOT, "Games", "CVS1J") if os.path.isdir(os.path.join(REPO_ROOT, "Games", "CVS1J")) else os.path.join(REPO_ROOT, "Games", "CVS1J_UNLOCK")
MAP_JSON_PATH = os.path.join(REPO_ROOT, "Docs", "CVS1_SOUNDTRACK_MAP.json")
OUTPUT_MP3_DIR = os.path.join(REPO_ROOT, "Extracted_Audio", "CVS1_MP3")

# Definición canónica de pistas de Capcom vs SNK 1
CVS1_TRACK_DEFINITIONS = [
    {"file": "ADX_0000.BIN", "role": "Osaka Stage - Capcom Side (Día)", "type": "stage", "desc": "Tema de escenario de Osaka (Día)"},
    {"file": "ADX_0001.BIN", "role": "Osaka Stage - SNK Side (Día)", "type": "stage", "desc": "Tema de escenario de Osaka SNK (Día)"},
    {"file": "ADX_0100.BIN", "role": "Aomori Bridge - Capcom Side (Noche)", "type": "stage", "desc": "Puente de Aomori Nocturno"},
    {"file": "ADX_0101.BIN", "role": "Aomori Bridge - SNK Side (Noche)", "type": "stage", "desc": "Puente de Aomori SNK"},
    {"file": "ADX_0200.BIN", "role": "Rooftop Dojo - Capcom Side (Atardecer)", "type": "stage", "desc": "Azotea al atardecer"},
    {"file": "ADX_0201.BIN", "role": "Rooftop Dojo - SNK Side (Atardecer)", "type": "stage", "desc": "Azotea SNK al atardecer"},
    {"file": "ADX_0300.BIN", "role": "Geese Howard Theme (Geese ni Shoyu)", "type": "boss", "desc": "Tema clásico de Geese Howard"},
    {"file": "ADX_0301.BIN", "role": "Geese Howard Intro", "type": "intro", "desc": "Entrada y presentación de Geese"},
    {"file": "ADX_0302.BIN", "role": "Geese Howard Jingle", "type": "jingle", "desc": "Jingle corto de Geese"},
    {"file": "ADX_0400.BIN", "role": "Vega / M. Bison Theme", "type": "boss", "desc": "Tema de jefe de Vega / Dictator"},
    {"file": "ADX_0401.BIN", "role": "Vega / M. Bison Intro", "type": "intro", "desc": "Entrada y presentación de Vega / M. Bison"},
    {"file": "ADX_0500.BIN", "role": "Special Match: Ryu vs. Kyo", "type": "stage", "desc": "Tema de rivalidad Ryu vs Kyo"},
    {"file": "ADX_0501.BIN", "role": "Special Match: Ryu vs. Kyo Intro", "type": "intro", "desc": "Intro del duelo Ryu vs Kyo"},
    {"file": "ADX_0600.BIN", "role": "Special Match: Iori vs. Kyo", "type": "stage", "desc": "Tema de rivalidad Iori vs Kyo"},
    {"file": "ADX_0601.BIN", "role": "Special Match: Iori vs. Kyo Intro", "type": "intro", "desc": "Intro del duelo Iori vs Kyo"},
    {"file": "ADX_0700.BIN", "role": "Gouki / Akuma Theme", "type": "boss", "desc": "Tema de jefe de Gouki / Akuma"},
    {"file": "ADX_0701.BIN", "role": "Gouki / Akuma Intro", "type": "intro", "desc": "Entrada de Gouki / Akuma"},
    {"file": "ADX_0800.BIN", "role": "Rugal Bernstein Theme", "type": "boss", "desc": "Tema de jefe de Rugal Bernstein"},
    {"file": "ADX_0801.BIN", "role": "Rugal Bernstein Intro", "type": "intro", "desc": "Entrada de Rugal Bernstein"},
    {"file": "ADX_0900.BIN", "role": "Final Tournament Stage", "type": "stage", "desc": "Escenario de la final del torneo"},
    {"file": "ADX_0901.BIN", "role": "Final Tournament Stage Intro", "type": "intro", "desc": "Intro del torneo final"},
    {"file": "ADX_0A00.BIN", "role": "Training Stage", "type": "stage", "desc": "Modo entrenamiento"},
    {"file": "ADX_0B00.BIN", "role": "Extra Stage: Pao Pao Cafe", "type": "stage", "desc": "Escenario extra Pao Pao Cafe"},
    {"file": "ADX_0B01.BIN", "role": "Extra Stage: Pao Pao Cafe Intro", "type": "intro", "desc": "Intro Pao Pao Cafe"},
    {"file": "ADX_0C00.BIN", "role": "Extra Stage: Metro City", "type": "stage", "desc": "Escenario extra Metro City (Final Fight)"},
    {"file": "ADX_0C01.BIN", "role": "Extra Stage: Metro City Intro", "type": "intro", "desc": "Intro Metro City"},
    {"file": "ADX_0D00.BIN", "role": "Extra Stage: Dojo", "type": "stage", "desc": "Escenario extra Dojo"},
    {"file": "ADX_0D01.BIN", "role": "Extra Stage: Dojo Intro", "type": "intro", "desc": "Intro Dojo"},
    {"file": "ADX_0E00.BIN", "role": "Extra Stage: Bonus Game", "type": "stage", "desc": "Minijuego / Bonus"},
    {"file": "ADX_0F00.BIN", "role": "Continue Screen", "type": "menu", "desc": "Pantalla de cuenta regresiva / Continue"},
    {"file": "ADX_1000.BIN", "role": "Game Over Screen", "type": "menu", "desc": "Pantalla de Game Over"},
    {"file": "ADX_1100.BIN", "role": "Character Select", "type": "menu", "desc": "Selector de Personajes"},
    {"file": "ADX_1200.BIN", "role": "Ratio / Order Select", "type": "menu", "desc": "Selección de Ratio y Orden de combate"},
    {"file": "ADX_1300.BIN", "role": "Victory / Win Screen", "type": "menu", "desc": "Pantalla de victoria tras la ronda"},
    {"file": "ADX_1400.BIN", "role": "Ranking / Score Screen", "type": "menu", "desc": "Pantalla de mejores puntuaciones"},
    {"file": "ADX_1500.BIN", "role": "Intermission / Next Match", "type": "menu", "desc": "Presentación del siguiente combate"},
    {"file": "ADX_1700.BIN", "role": "Opening Demo & Title", "type": "intro", "desc": "Intro del juego y pantalla de inicio (Press Start)"},
    {"file": "ADX_1800.BIN", "role": "Capcom Ending 1", "type": "ending", "desc": "Final lado Capcom"},
    {"file": "ADX_1900.BIN", "role": "SNK Ending 1", "type": "ending", "desc": "Final lado SNK"},
    {"file": "ADX_1A00.BIN", "role": "Ending Jingle 1", "type": "jingle", "desc": "Jingle de final 1"},
    {"file": "ADX_1B00.BIN", "role": "Capcom Logo Jingle", "type": "jingle", "desc": "Logo de Capcom al encender"},
    {"file": "ADX_1C00.BIN", "role": "Ending Jingle 3", "type": "jingle", "desc": "Jingle de final 3"},
    {"file": "ADX_1D00.BIN", "role": "Ending Jingle 4", "type": "jingle", "desc": "Jingle de final 4"},
    {"file": "ADX_1E00.BIN", "role": "Staff Roll / Credits (Capcom Side)", "type": "ending", "desc": "Créditos del equipo Capcom"},
    {"file": "ADX_1F00.BIN", "role": "Staff Roll / Credits (SNK Side)", "type": "ending", "desc": "Créditos del equipo SNK"},
    {"file": "ADX_2000.BIN", "role": "Secret Unlock Jingle 1", "type": "jingle", "desc": "Jingle de personaje secreto"},
    {"file": "ADX_2100.BIN", "role": "Secret Unlock Jingle 2", "type": "jingle", "desc": "Jingle de modo secreto"},
    {"file": "ADX_2200.BIN", "role": "Secret Unlock Jingle 3", "type": "jingle", "desc": "Jingle especial"},
]

def load_or_create_mapping() -> Dict[str, Any]:
    os.makedirs(os.path.dirname(MAP_JSON_PATH), exist_ok=True)
    if os.path.exists(MAP_JSON_PATH):
        try:
            with open(MAP_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error leyendo {MAP_JSON_PATH}: {e}")

    # Import canonical defaults from soundtrack_manager
    sys.path.insert(0, SCRIPT_DIR)
    import soundtrack_manager

    data = {
        "title": "Mapeo de Bandas Sonoras de Capcom vs SNK 1 (Japan / Millennium 2000)",
        "description": "Edita este archivo para configurar qué pista de audio de MvC2, CvS2, SSF2X, SF3 3rd Strike, Puzzle Fighter y FanDisk sonará para cada pista de CvS1.",
        "tracks": {}
    }

    for defn in CVS1_TRACK_DEFINITIONS:
        fname = defn["file"]
        canon = soundtrack_manager.CVS1_CANONICAL_MAP.get(fname, (
            "ADX_ST00.BIN", "ADX_S000.BIN", "02_B_NYC.ADX", "A_RYU_12.ADX", "Q01_SMOR.ADX", "ADX_TP00.BIN"
        ))
        data["tracks"][fname] = {
            "role": defn["role"],
            "type": defn["type"],
            "desc": defn["desc"],
            "targets": {
                "CVS2": canon[0],
                "MVC2": canon[1],
                "3S": canon[2],
                "ST": canon[3],
                "PF": canon[4],
                "FANDISK": canon[5],
            }
        }

    save_mapping_json(data)
    return data

def save_mapping_json(data: Dict[str, Any]):
    os.makedirs(os.path.dirname(MAP_JSON_PATH), exist_ok=True)
    with open(MAP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[✓] Archivo de mapeo guardado en: {MAP_JSON_PATH}")

def list_tracks():
    mapping_data = load_or_create_mapping()
    tracks = mapping_data["tracks"]

    print("=========================================================================================================================")
    print("   MAPA DE BANDAS SONORAS: CAPCOM VS SNK 1 (Millennium Fight 2000)")
    print("=========================================================================================================================")
    print(f"{'Archivo CvS1':<14} | {'Rol / Escenario':<38} | {'CvS2':<12} | {'MvC2':<12} | {'SSF2X':<12} | {'3rd Strike':<12}")
    print("-" * 121)

    for fname, info in tracks.items():
        role = info["role"]
        t = info["targets"]
        cvs2 = t.get("CVS2", "-")
        mvc2 = t.get("MVC2", "-")
        st = t.get("ST", "-")
        s3 = t.get("3S", "-")
        print(f"{fname:<14} | {role:<38} | {cvs2:<12} | {mvc2:<12} | {st:<12} | {s3:<12}")

    print("-" * 121)
    print(f"[*] Para modificar este mapeo, edita: {MAP_JSON_PATH}")
    print("[*] Luego ejecuta: python3 Tools/linux/cvs1_soundtrack_mapper.py apply")

def export_audio():
    os.makedirs(OUTPUT_MP3_DIR, exist_ok=True)
    print(f"[*] Exportando pistas ADX de CvS1 a MP3 en: {OUTPUT_MP3_DIR}")
    
    mapping_data = load_or_create_mapping()
    tracks = mapping_data["tracks"]
    
    count = 0
    for idx, (fname, info) in enumerate(tracks.items(), start=1):
        adx_path = os.path.join(CVS1_DIR, fname)
        if not os.path.exists(adx_path):
            continue
            
        clean_role = info["role"].replace(" ", "_").replace("/", "_").replace(":", "").replace("(", "").replace(")", "").replace(".", "")
        out_mp3_name = f"{idx:02d}_{fname[:-4]}_{clean_role}.mp3"
        out_mp3_path = os.path.join(OUTPUT_MP3_DIR, out_mp3_name)
        
        cmd = ["ffmpeg", "-y", "-i", adx_path, "-codec:a", "libmp3lame", "-b:a", "192k", out_mp3_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        count += 1
        print(f"  [✓] [{count:02d}/{len(tracks)}] Exportado: {out_mp3_name}")
        
    print(f"[✓] ¡{count} pistas exportadas con éxito! Puedes escucharlas directamente en: {OUTPUT_MP3_DIR}")

def apply_mapping():
    if not os.path.exists(MAP_JSON_PATH):
        print(f"[!] No existe el archivo {MAP_JSON_PATH}. Creándolo...")
        load_or_create_mapping()
        return

    with open(MAP_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Actualizar soundtrack_manager.py con el nuevo diccionario CVS1_CANONICAL_MAP
    st_mgr_path = os.path.join(SCRIPT_DIR, "soundtrack_manager.py")
    with open(st_mgr_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_tag = "CVS1_CANONICAL_MAP = {"
    end_tag = "}\n\nCVS1_SLOT_INDICES = {"

    if start_tag not in content or end_tag not in content:
        print("[!] No se encontró el bloque CVS1_CANONICAL_MAP en soundtrack_manager.py")
        return

    lines = [start_tag]
    for fname, info in data["tracks"].items():
        t = info["targets"]
        c2 = t.get("CVS2", "ADX_ST00.BIN")
        mv = t.get("MVC2", "ADX_S000.BIN")
        s3 = t.get("3S", "02_B_NYC.ADX")
        st = t.get("ST", "A_RYU_12.ADX")
        pf = t.get("PF", "Q01_SMOR.ADX")
        fd = t.get("FANDISK", "ADX_TP00.BIN")
        lines.append(f'    "{fname}": ("{c2}", "{mv}", "{s3}", "{st}", "{pf}", "{fd}"),')

    new_block = "\n".join(lines) + "\n"
    idx1 = content.find(start_tag)
    idx2 = content.find(end_tag)

    updated_content = content[:idx1] + new_block + content[idx2:]
    with open(st_mgr_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"[✓] ¡Mapeo actualizado con éxito en soundtrack_manager.py!")
    print("[✓] Tus cambios tendrán efecto inmediato en el próximo `make multidisc`.")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print("Uso: python3 Tools/linux/cvs1_soundtrack_mapper.py <comando>")
        print("Comandos:")
        print("  list         : Muestra el mapeo actual de pistas")
        print("  export-audio : Exporta todas las canciones de CvS1 a MP3")
        print("  edit         : Genera/actualiza el archivo Docs/CVS1_SOUNDTRACK_MAP.json")
        print("  apply        : Aplica los cambios de Docs/CVS1_SOUNDTRACK_MAP.json al compilador")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd in ("list", "show"):
        list_tracks()
    elif cmd in ("export-audio", "export", "mp3"):
        export_audio()
    elif cmd in ("edit", "json", "init"):
        load_or_create_mapping()
    elif cmd in ("apply", "save"):
        apply_mapping()
    else:
        print(f"[!] Comando desconocido: {cmd}")

if __name__ == "__main__":
    main()
