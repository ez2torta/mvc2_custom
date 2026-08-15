#!/usr/bin/env python3
"""
multidisc_manager.py - Wrapper de compatibilidad y punto de entrada para el motor multidisco de Dreamcast.
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from multidisc.cli import main

if __name__ == '__main__':
    main()
