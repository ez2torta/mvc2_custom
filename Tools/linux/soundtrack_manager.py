#!/usr/bin/env python3
"""
soundtrack_manager.py - Gestor y planificador de bandas sonoras cruzadas (Cross-Game Soundtracks)
para discos multijuego de Sega Dreamcast.

Permite que cualquier juego (MvC2, CvS2, Super Turbo, 3rd Strike, Puzzle Fighter) pueda
ejecutarse con la banda sonora de cualquiera de los otros juegos o en modo Silencioso (Silent),
utilizando enlaces duros (Shared Extents ISO9660) para ocupar 0 MB adicionales en el disco.
"""

import os
import sys
import shutil
import argparse
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
FRONTEND_DIR = os.path.join(REPO_ROOT, "Games", "Frontend")
ADXFILES_DIR = os.path.join(FRONTEND_DIR, "ADXFILES")
MAPPING_DIR = os.path.join(FRONTEND_DIR, "MAPPING")
DEFAULT_MAPPING_FILE = os.path.join(MAPPING_DIR, "SF2FD.LIST")

# Mapeo de columnas en SF2FD.LIST
# 0: ST (Super Turbo)
# 1: Loop Start
# 2: Loop End
# 3: Description / Role
# 4: MVC (Marvel vs Capcom 2)
# 5: 3S (Street Fighter III: 3rd Strike)
# 6: CVS (Capcom vs SNK 2)
# 7: PF (Puzzle Fighter)
# 8: (reserved / empty)
# 9: FD (FanDisk)
COLUMN_MAP = {
    "ST": 0,
    "SUPER_TURBO": 0,
    "SSF2X": 0,
    "MVC": 4,
    "MVC2": 4,
    "USAMVC": 4,
    "JAPMVC": 4,
    "VANILLA": 4,
    "ORIGINAL": 4,
    "NENE": 4,
    "CUSTOM": 4,
    "MVC_CUSTOM": 4,
    "3S": 5,
    "SF3": 5,
    "SF33": 5,
    "USA3S": 5,
    "JAP3S": 5,
    "CVS": 6,
    "CVS2": 6,
    "JAPCVS": 6,
    "CVS1": 6,
    "CVS1J": 6,
    "PF": 7,
    "SPF2X": 7,
    "FD": 9,
    "FANDISK": 9,
}

# Launcher directory mapping standard de TDCFinal2
STANDARD_LAUNCHER_MATRIX = {
    # target_game -> { soundtrack_name -> (dir_name, launcher_id, html_title) }
    "MVC2": {
        "NENE": ("GAME20", 20, "Marvel vs Capcom 2: Nene Edition (Custom Mod OST)"),
        "VANILLA": ("USAMVC", 7, "Marvel vs Capcom 2 (Original Vanilla Jazz OST)"),
        "SILENT": ("GAME25", 25, "Marvel vs Capcom 2 (Silent Mode / SFX Only)"),
        "CVS1": ("GAME23", 23, "Marvel vs Capcom 2 (Capcom vs SNK 1 OST)"),
        "PF": ("GAME24", 24, "Marvel vs Capcom 2 (Puzzle Fighter OST)"),
        "3S": ("GAME26", 26, "Marvel vs Capcom 2 (Street Fighter III 3rd Strike OST)"),
        "CVS2": ("GAME27", 27, "Marvel vs Capcom 2 (Capcom vs SNK 2 OST)"),
        "ST": ("GAME28", 28, "Marvel vs Capcom 2 (Super Street Fighter II Turbo OST)"),
        "FANDISK": ("GAME29", 29, "Marvel vs Capcom 2 (CvS FanDisk Remix OST)"),
    },
    "CVS1": {
        "ORIGINAL": ("CVS1J", 76, "Capcom vs SNK: Millennium Fight 2000 (Original OST)"),
        "SILENT": ("GAME75", 75, "Capcom vs SNK (Silent Mode / SFX Only)"),
        "NENE": ("GAME71", 71, "Capcom vs SNK (Marvel vs Capcom 2 Custom Nene OST)"),
        "VANILLA": ("GAME72", 72, "Capcom vs SNK (Marvel vs Capcom 2 Vanilla Jazz OST)"),
        "CVS2": ("GAME73", 73, "Capcom vs SNK (Capcom vs SNK 2 OST)"),
        "3S": ("GAME74", 74, "Capcom vs SNK (Street Fighter III 3rd Strike OST)"),
        "ST": ("GAME77", 77, "Capcom vs SNK (Super Street Fighter II Turbo OST)"),
        "PF": ("GAME78", 78, "Capcom vs SNK (Super Puzzle Fighter II X OST)"),
        "FANDISK": ("GAME79", 79, "Capcom vs SNK (CvS FanDisk Remix OST)"),
    },
    "JAPMVC": {
        "ORIGINAL": ("JAPMVC", 9, "Marvel vs Capcom 2 Jap (Original OST)"),
        "SILENT": ("GAME30", 30, "Marvel vs Capcom 2 Jap (Silent Mode)"),
        "CVS2": ("GAME34", 34, "Marvel vs Capcom 2 Jap (CvS2 OST)"),
        "PF": ("GAME36", 36, "Marvel vs Capcom 2 Jap (Puzzle Fighter OST)"),
        "ST": ("GAME37", 37, "Marvel vs Capcom 2 Jap (Super Turbo OST)"),
        "3S": ("GAME38", 38, "Marvel vs Capcom 2 Jap (3rd Strike OST)"),
        "FANDISK": ("GAME39", 39, "Marvel vs Capcom 2 Jap (FanDisk OST)"),
    },
    "CVS2": {
        "ORIGINAL": ("JAPCVS", 3, "Capcom vs SNK 2 (Original OST)"),
        "SILENT": ("GAME40", 40, "Capcom vs SNK 2 (Silent Mode)"),
        "CVS1": ("GAME41", 41, "Capcom vs SNK 2 (Capcom vs SNK 1 OST)"),
        "FANDISK": ("GAME42", 42, "Capcom vs SNK 2 (FanDisk OST)"),
        "NENE": ("GAME45", 45, "Capcom vs SNK 2 (Marvel vs Capcom 2 Custom Nene OST)"),
        "3S": ("GAME46", 46, "Capcom vs SNK 2 (Street Fighter III 3rd Strike OST)"),
        "VANILLA": ("GAME47", 47, "Capcom vs SNK 2 (Marvel vs Capcom 2 Vanilla Jazz OST)"),
        "MVC2": ("GAME47", 47, "Capcom vs SNK 2 (Marvel vs Capcom 2 Vanilla Jazz OST)"),
        "ST": ("GAME48", 48, "Capcom vs SNK 2 (Super Street Fighter II Turbo OST)"),
        "PF": ("GAME49", 49, "Capcom vs SNK 2 (Puzzle Fighter OST)"),
    },
    "3S": {
        "ORIGINAL": ("USA3S", 6, "Street Fighter III: 3rd Strike (Original OST)"),
        "SILENT": ("GAME50", 50, "Street Fighter III: 3rd Strike (Silent Mode)"),
        "ST": ("GAME52", 52, "Street Fighter III: 3rd Strike (Super Turbo OST)"),
        "MVC2": ("GAME56", 56, "Street Fighter III: 3rd Strike (Marvel vs Capcom 2 OST)"),
        "CVS2": ("GAME57", 57, "Street Fighter III: 3rd Strike (Capcom vs SNK 2 OST)"),
        "PF": ("GAME58", 58, "Street Fighter III: 3rd Strike (Puzzle Fighter OST)"),
        "FANDISK": ("GAME59", 59, "Street Fighter III: 3rd Strike (FanDisk OST)"),
    },
    "PF": {
        "ORIGINAL": ("PF", 4, "Super Puzzle Fighter II X (Original OST)"),
        "SILENT": ("GAME70", 70, "Super Puzzle Fighter II X (Silent Mode)"),
        "MVC2": ("GAME72", 72, "Super Puzzle Fighter II X (Marvel vs Capcom 2 OST)"),
        "3S": ("GAME74", 74, "Super Puzzle Fighter II X (3rd Strike OST)"),
        "CVS2": ("GAME76", 76, "Super Puzzle Fighter II X (Capcom vs SNK 2 OST)"),
        "ST": ("GAME78", 78, "Super Puzzle Fighter II X (Super Turbo OST)"),
        "FANDISK": ("GAME79", 79, "Super Puzzle Fighter II X (FanDisk OST)"),
    },
    "ST": {
        "ORIGINAL": ("ST", 5, "Super Street Fighter II X (Original OST)"),
        "SILENT": ("GAME80", 80, "Super Street Fighter II X (Silent Mode)"),
        "CVS1": ("GAME81", 81, "Super Street Fighter II X (Capcom vs SNK 1 OST)"),
        "VANILLA": ("GAME82", 82, "Super Street Fighter II X (Marvel vs Capcom 2 Vanilla Jazz OST)"),
        "MVC2": ("GAME82", 82, "Super Street Fighter II X (Marvel vs Capcom 2 Vanilla Jazz OST)"),
        "NENE": ("GAME83", 83, "Super Street Fighter II X (Marvel vs Capcom 2 Custom Nene OST)"),
        "3S": ("GAME84", 84, "Super Street Fighter II X (3rd Strike OST)"),
        "CVS2": ("GAME86", 86, "Super Street Fighter II X (Capcom vs SNK 2 OST)"),
        "PF": ("GAME87", 87, "Super Street Fighter II X (Puzzle Fighter OST)"),
        "FANDISK": ("GAME89", 89, "Super Street Fighter II X (FanDisk OST)"),
    }
}

# Mapeo canónico explícito para Capcom vs SNK 1 (Japan)
# Formato: cvs1_track: (cvs2, mvc2, 3s, st, pf, fandisk)
CVS1_CANONICAL_MAP = {
    "ADX_0000.BIN": ("ADX_ST00.BIN", "ADX_S000.BIN", "02_B_NYC.ADX", "A_BAR_1A.ADX", "Q01_SMOR.ADX", "ADX_TP00.BIN"),
    "ADX_0001.BIN": ("ADX_ST01.BIN", "ADX_S010.BIN", "05_B_ROS.ADX", "A_BIS_19.ADX", "Q02_SCHU.ADX", "ADX_TP01.BIN"),
    "ADX_0100.BIN": ("ADX_ST02.BIN", "ADX_S020.BIN", "09_C_GEM.ADX", "A_BLA_15.ADX", "Q03_SRYU.ADX", "ADX_TP02.BIN"),
    "ADX_0101.BIN": ("ADX_ST03.BIN", "ADX_S030.BIN", "12_C_CHI.ADX", "A_CAM_1E.ADX", "Q04_SKEN.ADX", "ADX_TP03.BIN"),
    "ADX_0200.BIN": ("ADX_ST04.BIN", "ADX_S040.BIN", "14_B_SHI.ADX", "A_CHU_14.ADX", "Q05_SLEI.ADX", "ADX_TP04.BIN"),
    "ADX_0201.BIN": ("ADX_ST05.BIN", "ADX_S050.BIN", "18_C_KYO.ADX", "A_DEE_20.ADX", "Q06_SDON.ADX", "ADX_TP05.BIN"),
    "ADX_0300.BIN": ("ADX_ST06.BIN", "ADX_S060.BIN", "21_C_DOJ.ADX", "A_DHA_18.ADX", "Q07_SFEL.ADX", "ADX_TP06.BIN"),
    "ADX_0301.BIN": ("ADX_ST06.BIN", "ADX_S060.BIN", "21_C_DOJ.ADX", "A_DHA_18.ADX", "Q07_SFEL.ADX", "ADX_TP06.BIN"),
    "ADX_0400.BIN": ("ADX_ST07.BIN", "ADX_S070.BIN", "22_A_YAM.ADX", "A_FEI_1D.ADX", "Q08_SSAK.ADX", "ADX_TP07.BIN"),
    "ADX_0401.BIN": ("ADX_ST07.BIN", "ADX_S070.BIN", "22_A_YAM.ADX", "A_FEI_1D.ADX", "Q08_SSAK.ADX", "ADX_TP07.BIN"),
    "ADX_0500.BIN": ("ADX_ST08.BIN", "ADX_S080.BIN", "25_A_AFR.ADX", "A_GOU_D6.ADX", "Q09_SDEV.ADX", "ADX_TP08.BIN"),
    "ADX_0501.BIN": ("ADX_ST08.BIN", "ADX_S080.BIN", "25_A_AFR.ADX", "A_GOU_D6.ADX", "Q09_SDEV.ADX", "ADX_TP08.BIN"),
    "ADX_0600.BIN": ("ADX_ST09.BIN", "ADX_S090.BIN", "30_C_BRA.ADX", "A_GUI_17.ADX", "Q0A_SGOU.ADX", "ADX_TP09.BIN"),
    "ADX_0601.BIN": ("ADX_ST09.BIN", "ADX_S090.BIN", "30_C_BRA.ADX", "A_GUI_17.ADX", "Q0A_SGOU.ADX", "ADX_TP09.BIN"),
    "ADX_0700.BIN": ("ADX_ST0A.BIN", "ADX_S0A0.BIN", "32_B_LON.ADX", "A_HON_13.ADX", "Q0B_DANT.ADX", "ADX_TP0A.BIN"),
    "ADX_0701.BIN": ("ADX_ST0A.BIN", "ADX_S0A0.BIN", "32_B_LON.ADX", "A_HON_13.ADX", "Q0B_DANT.ADX", "ADX_TP0A.BIN"),
    "ADX_0800.BIN": ("ADX_ST0B.BIN", "ADX_S0B0.BIN", "35_B_HON.ADX", "A_KEN_11.ADX", "Q0D_PLAY.ADX", "ADX_TP0B.BIN"),
    "ADX_0801.BIN": ("ADX_ST0B.BIN", "ADX_S0B0.BIN", "35_B_HON.ADX", "A_KEN_11.ADX", "Q0D_PLAY.ADX", "ADX_TP0B.BIN"),
    "ADX_0900.BIN": ("ADX_ST00.BIN", "ADX_S000.BIN", "40_A_Q.ADX", "A_VEG_1C.ADX", "Q11_SDEM.ADX", "ADX_FD08.BIN"),
    "ADX_0901.BIN": ("ADX_ST00.BIN", "ADX_S000.BIN", "40_A_Q.ADX", "A_VEG_1C.ADX", "Q11_SDEM.ADX", "ADX_FD08.BIN"),
    "ADX_0A00.BIN": ("ADX_ST05.BIN", "ADX_S050.BIN", "61_BO1.ADX", "BONUS_3B.ADX", "Q07_SFEL.ADX", "ADX_FD0D.BIN"),
    "ADX_0B00.BIN": ("ADX_ST01.BIN", "ADX_S010.BIN", "37_A_FRA.ADX", "A_RYU_12.ADX", "Q03_SRYU.ADX", "ADX_TP0C.BIN"),
    "ADX_0B01.BIN": ("ADX_ST01.BIN", "ADX_S010.BIN", "37_A_FRA.ADX", "A_RYU_12.ADX", "Q03_SRYU.ADX", "ADX_TP0C.BIN"),
    "ADX_0C00.BIN": ("ADX_ST02.BIN", "ADX_S020.BIN", "44_B_MEX.ADX", "A_THA_1F.ADX", "Q04_SKEN.ADX", "ADX_FD0A.BIN"),
    "ADX_0C01.BIN": ("ADX_ST02.BIN", "ADX_S020.BIN", "44_B_MEX.ADX", "A_THA_1F.ADX", "Q04_SKEN.ADX", "ADX_FD0A.BIN"),
    "ADX_0D00.BIN": ("ADX_ST03.BIN", "ADX_S030.BIN", "46_A_GRE.ADX", "A_ZAN_16.ADX", "Q06_SDON.ADX", "ADX_FD0C.BIN"),
    "ADX_0D01.BIN": ("ADX_ST03.BIN", "ADX_S030.BIN", "46_A_GRE.ADX", "A_ZAN_16.ADX", "Q06_SDON.ADX", "ADX_FD0C.BIN"),
    "ADX_0E00.BIN": ("ADX_ST07.BIN", "ADX_S070.BIN", "62_BO2.ADX", "A_SAG_1B.ADX", "Q08_SSAK.ADX", "ADX_FD0B.BIN"),
    "ADX_1100.BIN": ("ADX_SEL1.BIN", "ADX_SELC.BIN", "53_P_SEL.ADX", "P_SEL_34.ADX", "Q0E_SELE.ADX", "ADX_MENU.BIN"),
    "ADX_1200.BIN": ("ADX_RATO.BIN", "ADX_MENU.BIN", "57_S_SEL.ADX", "VS_35.ADX", "Q0E_SELE.ADX", "ADX_MENU.BIN"),
    "ADX_1300.BIN": ("ADX_WIN5.BIN", "ADX_WINS.BIN", "55_WIN.ADX", "CONG2_D2.ADX", "Q10_WINN.ADX", "ADX_FD00.BIN"),
    "ADX_0F00.BIN": ("ADX_CONT.BIN", "ADX_CONT.BIN", "58_CONTI.ADX", "CONTI_37.ADX", "Q12_CONT.ADX", "ADX_FD01.BIN"),
    "ADX_1000.BIN": ("ADX_OVER.BIN", "ADX_OVER.BIN", "59_OVER.ADX", "GAME_39.ADX", "Q14_OVER.ADX", "ADX_FD02.BIN"),
    "ADX_1700.BIN": ("ADX_OPEN.BIN", "ADX_OPEN.BIN", "52_OPEN.ADX", "DEMO_33.ADX", "Q0C_OPEN.ADX", "ADX_OPEN.BIN"),
    "ADX_1E00.BIN": ("ADX_END1.BIN", "ADX_STAF.BIN", "49_END.ADX", "E_RYU_23.ADX", "Q17_ENDN.ADX", "ADX_TP00.BIN"),
    "ADX_1F00.BIN": ("ADX_END2.BIN", "ADX_STAF.BIN", "50_END.ADX", "E_KEN_21.ADX", "Q17_ENDN.ADX", "ADX_TP01.BIN"),
}

CVS1_SLOT_INDICES = {
    "CVS2": 0, "CVS": 0, "JAPCVS": 0,
    "MVC2": 1, "MVC": 1, "USAMVC": 1, "JAPMVC": 1, "NENE": 1, "VANILLA": 1, "CUSTOM": 1,
    "3S": 2, "SF3": 2, "SF33": 2, "USA3S": 2, "JAP3S": 2,
    "ST": 3, "SSF2X": 3, "SUPER_TURBO": 3,
    "PF": 4, "SPF2X": 4,
    "FD": 5, "FANDISK": 5,
}

# Mapeo exacto configurado según orden.md para cuando otros juegos usan el OST de CvS1
CVS1_OST_OVERLAY_FOR_TARGET = {
    # Marvel vs Capcom 2
    "MVC2": {
        "ADX_S000.BIN": "ADX_0800.BIN", # Rugal Bernstein Theme
        "ADX_S010.BIN": "ADX_0600.BIN", # Special Match: Iori vs Kyo
        "ADX_S020.BIN": "ADX_0500.BIN", # Special Match: Ryu vs Kyo
        "ADX_S030.BIN": "ADX_0300.BIN", # Geese Howard Theme
        "ADX_S040.BIN": "ADX_0200.BIN", # Rooftop Dusk Capcom
        "ADX_S050.BIN": "ADX_0100.BIN", # Aomori Bridge Night Capcom
        "ADX_S060.BIN": "ADX_0300.BIN", # Geese Howard Theme
        "ADX_S070.BIN": "ADX_0400.BIN", # Vega/Bison Theme
        "ADX_S080.BIN": "ADX_0500.BIN", # Ryu vs Kyo Match
        "ADX_S090.BIN": "ADX_0600.BIN", # Iori vs Kyo Match
        "ADX_S0A0.BIN": "ADX_0700.BIN", # Gouki Akuma Theme
        "ADX_S0B0.BIN": "ADX_0B00.BIN", # Extra Stage Paopao Cafe
        "ADX_SELC.BIN": "ADX_1100.BIN", # Character Select
        "ADX_MENU.BIN": "ADX_1200.BIN", # Ratio / Order Select
        "ADX_WINS.BIN": "ADX_1300.BIN", # Victory Screen
        "ADX_CONT.BIN": "ADX_0F00.BIN", # Continue Screen
        "ADX_OVER.BIN": "ADX_1000.BIN", # Game Over Screen
        "ADX_OPEN.BIN": "ADX_1700.BIN", # Opening Demo Title
        "ADX_STAF.BIN": "ADX_1700.BIN", # Credits / Ending
    },
    # Capcom vs SNK 2
    "CVS2": {
        "ADX_ST00.BIN": "ADX_0800.BIN", # Rugal Bernstein Theme
        "ADX_ST01.BIN": "ADX_0600.BIN", # Special Match: Iori vs Kyo
        "ADX_ST02.BIN": "ADX_0500.BIN", # Special Match: Ryu vs Kyo
        "ADX_ST03.BIN": "ADX_0300.BIN", # Geese Howard Theme
        "ADX_ST04.BIN": "ADX_0200.BIN", # Rooftop Dusk Capcom
        "ADX_ST05.BIN": "ADX_0100.BIN", # Aomori Bridge Night Capcom
        "ADX_ST06.BIN": "ADX_0300.BIN", # Geese Howard Theme
        "ADX_ST07.BIN": "ADX_0400.BIN", # Vega/Bison Theme
        "ADX_ST08.BIN": "ADX_0500.BIN", # Ryu vs Kyo Match
        "ADX_ST09.BIN": "ADX_0600.BIN", # Iori vs Kyo Match
        "ADX_ST0A.BIN": "ADX_0700.BIN", # Gouki Akuma Theme
        "ADX_ST0B.BIN": "ADX_0B00.BIN", # Extra Stage Paopao Cafe
        "ADX_FNAL.BIN": "ADX_0D00.BIN", # Extra Stage Dojo
        "ADX_SEL1.BIN": "ADX_1100.BIN", # Character Select
        "ADX_SEL2.BIN": "ADX_1100.BIN", # Character Select
        "ADX_RATO.BIN": "ADX_1200.BIN", # Ratio Select
        "ADX_WIN1.BIN": "ADX_1300.BIN", # Victory Screen
        "ADX_WIN2.BIN": "ADX_1300.BIN",
        "ADX_WIN3.BIN": "ADX_1300.BIN",
        "ADX_WIN4.BIN": "ADX_1300.BIN",
        "ADX_WIN5.BIN": "ADX_1300.BIN",
        "ADX_CONT.BIN": "ADX_0F00.BIN", # Continue Screen
        "ADX_OVER.BIN": "ADX_1000.BIN", # Game Over Screen
        "ADX_OPEN.BIN": "ADX_1700.BIN", # Opening Demo Title
        "ADX_END1.BIN": "ADX_1700.BIN", # Credits / Ending
        "ADX_END2.BIN": "ADX_1700.BIN",
    },
    # Super Street Fighter II Turbo
    "ST": {
        "A_RYU_12.ADX": "ADX_0500.BIN", # Ryu vs Kyo
        "A_KEN_11.ADX": "ADX_0800.BIN", # Rugal
        "A_GUI_17.ADX": "ADX_0600.BIN", # Iori vs Kyo
        "A_CHU_14.ADX": "ADX_0200.BIN", # Rooftop
        "A_DHA_18.ADX": "ADX_0300.BIN", # Geese Howard
        "A_ZAN_16.ADX": "ADX_0100.BIN", # Aomori Bridge Night
        "A_BLA_15.ADX": "ADX_0000.BIN", # Osaka Day
        "A_HON_13.ADX": "ADX_0D00.BIN", # Extra Dojo
        "A_CAM_1E.ADX": "ADX_0B00.BIN", # Paopao Cafe
        "A_FEI_1D.ADX": "ADX_0C00.BIN", # Metro City
        "A_DEE_20.ADX": "ADX_0201.BIN", # Rooftop Dusk SNK
        "A_THA_1F.ADX": "ADX_0101.BIN", # Aomori Bridge Night SNK
        "A_BAR_1A.ADX": "ADX_0800.BIN", # Rugal
        "A_SAG_1B.ADX": "ADX_0D00.BIN", # Extra Dojo
        "A_VEG_1C.ADX": "ADX_0300.BIN", # Geese Howard
        "A_BIS_19.ADX": "ADX_0400.BIN", # Vega/Bison
        "A_GOU_D6.ADX": "ADX_0700.BIN", # Gouki Akuma
        "P_SEL_34.ADX": "ADX_1100.BIN", # Character Select
        "VS_35.ADX":    "ADX_1200.BIN", # Ratio/Order Select
        "CONG2_D2.ADX": "ADX_1300.BIN", # Victory Screen
        "CONTI_37.ADX": "ADX_0F00.BIN", # Continue Screen
        "GAME_39.ADX":  "ADX_1000.BIN", # Game Over Screen
        "DEMO_33.ADX":  "ADX_1700.BIN", # Opening Demo Title
        "E_RYU_23.ADX": "ADX_1700.BIN", # Ending
        "E_KEN_21.ADX": "ADX_1700.BIN",
    }
}

class SoundtrackMatrix:
    def __init__(self, mapping_filepath: str = DEFAULT_MAPPING_FILE):
        self.mapping_file = mapping_filepath
        self.entries = []
        self._load_matrix()

    def _load_matrix(self):
        if not os.path.isfile(self.mapping_file):
            return
        with open(self.mapping_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.rstrip("\r\n")
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("\t")]
                # Validar que la fila contiene archivos de audio reales (no nombres de columnas como MVC, 3S, etc.)
                first_item = parts[0] if parts else ""
                has_audio_ext = any(p.upper().endswith(".ADX") or p.upper().endswith(".BIN") for p in parts if p)
                if not has_audio_ext:
                    continue
                self.entries.append(parts)

    def get_track_mapping(self, target_game: str, source_soundtrack: str) -> Dict[str, str]:
        """
        Retorna un diccionario { target_track_filename: source_track_filename }
        para sustituir la música del juego objetivo con la banda sonora elegida.
        """
        target_upper = target_game.upper()
        source_upper = source_soundtrack.upper()
        
        mapping = {}
        
        if source_upper in ("SILENT", "MUTE", "NONE"):
            # En modo Silent, todos los tracks apuntan al track nulo 0BYTE.ADX
            if target_upper in ("CVS1", "CVS1J"):
                for cvs1_f in CVS1_CANONICAL_MAP.keys():
                    mapping[cvs1_f] = "0BYTE.ADX"
                return mapping
            target_col = COLUMN_MAP.get(target_upper)
            if target_col is not None:
                for row in self.entries:
                    if len(row) > target_col:
                        t_track = row[target_col].strip()
                        if t_track and (t_track.upper().endswith(".ADX") or t_track.upper().endswith(".BIN")):
                            mapping[t_track] = "0BYTE.ADX"
            return mapping

        # 1. Caso Especial: CvS1 como juego destino
        if target_upper in ("CVS1", "CVS1J"):
            slot_idx = CVS1_SLOT_INDICES.get(source_upper)
            if slot_idx is not None:
                for cvs1_track, variants in CVS1_CANONICAL_MAP.items():
                    mapping[cvs1_track] = variants[slot_idx]
                return mapping

        # 2. Caso Especial: CvS1 como soundtrack origen para otros juegos
        if source_upper in ("CVS1", "CVS1J"):
            target_key = "MVC2" if target_upper in ("MVC2", "MVC", "USAMVC", "NENE") else ("CVS2" if target_upper in ("CVS2", "CVS", "JAPCVS") else ("ST" if target_upper in ("ST", "SSF2X", "SUPER_TURBO") else None))
            if target_key and target_key in CVS1_OST_OVERLAY_FOR_TARGET:
                return dict(CVS1_OST_OVERLAY_FOR_TARGET[target_key])
            slot_idx = CVS1_SLOT_INDICES.get(target_upper)
            if slot_idx is not None:
                for cvs1_track, variants in CVS1_CANONICAL_MAP.items():
                    target_track = variants[slot_idx]
                    mapping[target_track] = cvs1_track
                return mapping

        target_col = COLUMN_MAP.get(target_upper)
        source_col = COLUMN_MAP.get(source_upper)
        
        if target_col is None:
            raise ValueError(f"Juego objetivo no soportado: {target_game}. Soportados: {list(COLUMN_MAP.keys())}")
            
        if source_col is None:
            raise ValueError(f"Soundtrack de origen no soportado: {source_soundtrack}")
            
        for row in self.entries:
            if len(row) > max(target_col, source_col):
                t_track = row[target_col].strip()
                s_track = row[source_col].strip()
                if not t_track or not s_track:
                    continue
                    
                if not s_track.upper().endswith(".ADX") and not s_track.upper().endswith(".BIN"):
                    s_track = s_track + ".ADX"
                if not t_track.upper().endswith(".ADX") and not t_track.upper().endswith(".BIN"):
                    t_track = t_track + ".ADX"
                    
                if t_track.upper() in COLUMN_MAP or s_track.upper() in COLUMN_MAP:
                    continue
                    
                mapping[t_track] = s_track
                    
        return mapping

    def get_soundtrack_source_dir(self, source_soundtrack: str, adx_base_dir: str = ADXFILES_DIR) -> str:
        """Devuelve la carpeta fuente de los archivos ADX del soundtrack correspondiente."""
        st_upper = source_soundtrack.upper()
        folder_map = {
            "3S": "3S",
            "SF3": "3S",
            "SF33": "3S",
            "USA3S": "3S",
            "JAP3S": "3S",
            "CVS": "CVS",
            "CVS2": "CVS",
            "JAPCVS": "CVS",
            "CVS1": "CVS1",
            "CVS1J": "CVS1",
            "MVC": "MVC",
            "MVC2": "MVC",
            "USAMVC": "MVC",
            "JAPMVC": "MVC",
            "VANILLA": "MVC",
            "ORIGINAL": "MVC",
            "NENE": "MVC_CUSTOM",
            "CUSTOM": "MVC_CUSTOM",
            "MVC_CUSTOM": "MVC_CUSTOM",
            "PF": "PF",
            "SPF2X": "PF",
            "ST": "ST",
            "SSF2X": "ST",
            "SUPER_TURBO": "ST",
            "FD": "FANDISK",
            "FANDISK": "FANDISK",
            "SILENT": "",
        }
        sub = folder_map.get(st_upper, st_upper)
        return os.path.join(adx_base_dir, sub) if sub else adx_base_dir

def generate_mixed_game_directory(
    base_game_dir: str,
    output_game_dir: str,
    target_game_key: str,
    soundtrack_key: str,
    matrix: Optional[SoundtrackMatrix] = None,
    adx_pool_dir: str = ADXFILES_DIR,
    verbose: bool = True
) -> bool:
    """
    Crea una variante de juego con banda sonora personalizada mediante hardlinks.
    - Todos los binarios, texturas y datos del juego base se enlazan con hardlink (0 MB).
    - Los archivos ADX se sustituyen por hardlinks a los tracks de la banda sonora destino.
    """
    if matrix is None:
        matrix = SoundtrackMatrix()
        
    if not os.path.isdir(base_game_dir):
        print(f"[!] Error: El directorio base de juego '{base_game_dir}' no existe.")
        return False
        
    os.makedirs(output_game_dir, exist_ok=True)
    
    # 1. Obtener mapeo de pistas
    track_map = matrix.get_track_mapping(target_game_key, soundtrack_key)
    source_adx_dir = matrix.get_soundtrack_source_dir(soundtrack_key, adx_pool_dir)
    zero_byte_adx = os.path.join(adx_pool_dir, "0BYTE.ADX")
    if not os.path.exists(zero_byte_adx):
        os.makedirs(os.path.dirname(os.path.abspath(zero_byte_adx)), exist_ok=True)
        with open(zero_byte_adx, "wb") as f:
            pass # Archivo de 0 bytes
            
    if verbose:
        print(f"[*] Creando variante de juego con Soundtrack: {target_game_key} + {soundtrack_key} OST")
        print(f"    Juego Base: {base_game_dir}")
        print(f"    Destino   : {output_game_dir}")
        print(f"    Pistas Mapeadas: {len(track_map)}")
        
    # 2. Hardlinkear todos los archivos del juego base
    is_same_dir = os.path.abspath(base_game_dir) == os.path.abspath(output_game_dir)
    if not is_same_dir:
        for root, dirs, files in os.walk(base_game_dir):
            rel_dir = os.path.relpath(root, base_game_dir)
            dest_subdir = os.path.join(output_game_dir, rel_dir) if rel_dir != "." else output_game_dir
            os.makedirs(dest_subdir, exist_ok=True)
            
            for f in files:
                src_f = os.path.join(root, f)
                dest_f = os.path.join(dest_subdir, f)
                
                if os.path.exists(dest_f):
                    os.remove(dest_f)
                try:
                    os.link(src_f, dest_f)
                except OSError:
                    shutil.copy2(src_f, dest_f)
                
    # 3. Inyectar pistas de audio de la banda sonora destino
    injected_tracks = 0
    for target_track, source_track in track_map.items():
        dest_path = os.path.join(output_game_dir, target_track)
        
        if soundtrack_key.upper() in ("SILENT", "MUTE", "NONE") or source_track == "0BYTE.ADX":
            src_path = zero_byte_adx
        else:
            src_path = os.path.join(source_adx_dir, source_track)
            if not os.path.exists(src_path):
                # Probar extension .BIN / .ADX cruzada
                alt_track = source_track.replace(".ADX", ".BIN") if source_track.endswith(".ADX") else source_track.replace(".BIN", ".ADX")
                alt_path = os.path.join(source_adx_dir, alt_track)
                if os.path.exists(alt_path):
                    src_path = alt_path
                else:
                    # Buscar en raíz de adx_pool_dir
                    root_path = os.path.join(adx_pool_dir, source_track)
                    if os.path.exists(root_path):
                        src_path = root_path
                    else:
                        if verbose:
                            print(f"[!] Aviso: Pista fuente no encontrada '{src_path}'. Saltando.")
                        continue
                        
        if os.path.exists(dest_path):
            os.remove(dest_path)
            
        try:
            os.link(src_path, dest_path)
            injected_tracks += 1
        except OSError:
            shutil.copy2(src_path, dest_path)
            injected_tracks += 1
            
    if verbose:
        print(f"[✓] Variante lista en '{output_game_dir}': {injected_tracks} pistas vinculadas.")
    return True

def generate_all_soundtrack_variants_for_game(
    target_game_key: str,
    base_game_dir: str,
    staging_dir: str,
    adx_pool_dir: str = ADXFILES_DIR,
    verbose: bool = True
) -> Dict[str, str]:
    """
    Genera automáticamente todas las variantes de banda sonora para un juego según la matriz canónica.
    """
    game_variants = STANDARD_LAUNCHER_MATRIX.get(target_game_key.upper(), {})
    if not game_variants:
        print(f"[!] No hay matriz estándar registrada para '{target_game_key}'.")
        return {}
        
    created_dirs = {}
    matrix = SoundtrackMatrix()
    
    print(f"========================================================================")
    print(f"    Generación de Variantes de Soundtrack para: {target_game_key}")
    print(f"========================================================================")
    
    for st_name, (dir_name, launcher_id, title) in game_variants.items():
        if st_name == "ORIGINAL":
            continue # La versión original ya existe
            
        out_dir = os.path.join(staging_dir, dir_name)
        ok = generate_mixed_game_directory(
            base_game_dir=base_game_dir,
            output_game_dir=out_dir,
            target_game_key=target_game_key,
            soundtrack_key=st_name,
            matrix=matrix,
            adx_pool_dir=adx_pool_dir,
            verbose=verbose
        )
        if ok:
            created_dirs[st_name] = out_dir
            
    print(f"[✓] Total de variantes generadas: {len(created_dirs)}")
    return created_dirs

def print_soundtrack_matrix_table(target_game: Optional[str] = None):
    """Imprime en consola la tabla de combinaciones y launchers disponibles."""
    print("=================================================================================")
    print("        TABLA MAESTRA DE SOUNDTRACKS CRUZADOS (TDCFINAL2 / MULTIDISC)")
    print("=================================================================================")
    print(f"{'Juego Base':<10} | {'Soundtrack':<10} | {'Directorio':<10} | {'Launcher':<8} | {'Título del Menú'}")
    print("-" * 81)
    
    for g_key, variants in STANDARD_LAUNCHER_MATRIX.items():
        if target_game and g_key.upper() != target_game.upper():
            continue
        for st_key, (dirname, lid, title) in variants.items():
            print(f"{g_key:<10} | {st_key:<10} | {dirname:<10} | [{lid:2d}]     | {title}")
        print("-" * 81)

def main():
    parser = argparse.ArgumentParser(description="Soundtrack Manager & Cross-Game Audio Matrix para Sega Dreamcast.")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Subcomando: table / list
    subparsers.add_parser("list", help="Muestra la tabla de compatibilidad y launchers")
    
    # Subcomando: mix
    mix_p = subparsers.add_parser("mix", help="Genera una variante con soundtrack cruzado")
    mix_p.add_argument("--game", required=True, help="Juego objetivo (MVC2, CVS2, SSF2X, 3S, PF)")
    mix_p.add_argument("--soundtrack", required=True, help="Banda sonora deseada (3S, CVS2, ST, PF, MVC2, SILENT)")
    mix_p.add_argument("--base-dir", required=True, help="Directorio del juego base")
    mix_p.add_argument("--out-dir", required=True, help="Directorio destino para la variante")
    mix_p.add_argument("--adx-pool", default=ADXFILES_DIR, help="Directorio con los archivos ADX fuente")
    
    # Subcomando: generate-all
    all_p = subparsers.add_parser("generate-all", help="Genera todas las variantes de un juego")
    all_p.add_argument("--game", required=True, help="Juego objetivo (MVC2, CVS2, SSF2X, 3S, PF)")
    all_p.add_argument("--base-dir", required=True, help="Directorio del juego base")
    all_p.add_argument("--staging-dir", required=True, help="Directorio staging donde colocar GAME20, GAME24, etc.")
    all_p.add_argument("--adx-pool", default=ADXFILES_DIR, help="Directorio con los archivos ADX fuente")
    
    args = parser.parse_args()
    
    if args.command == "list" or not args.command:
        print_soundtrack_matrix_table()
    elif args.command == "mix":
        ok = generate_mixed_game_directory(
            base_game_dir=args.base_dir,
            output_game_dir=args.out_dir,
            target_game_key=args.game,
            soundtrack_key=args.soundtrack,
            adx_pool_dir=args.adx_pool,
            verbose=True
        )
        sys.exit(0 if ok else 1)
    elif args.command == "generate-all":
        res = generate_all_soundtrack_variants_for_game(
            target_game_key=args.game,
            base_game_dir=args.base_dir,
            staging_dir=args.staging_dir,
            adx_pool_dir=args.adx_pool,
            verbose=True
        )
        sys.exit(0 if res else 1)

if __name__ == "__main__":
    main()
