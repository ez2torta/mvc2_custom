# Marvel vs Capcom 2 - Custom Modding & Build Pipeline (Dreamcast)

Repositorio con los datos y herramientas completas para modding, extracción/inyección de texturas y audio, y compilación a imágenes de **SEGA Dreamcast** (**GDI** y **CDI**) en Linux y Windows.

---

## 🚀 Comandos Rápidos (Makefile)

Desde la raíz del repositorio puedes ejecutar:

```bash
# Ver todos los comandos disponibles
make help

# --- TEXTURAS ---
# 1. Extraer TODAS las texturas a PNG (Extracted_Textures/)
make extract-textures

# 2. Reinyectar las texturas PNG modificadas a MVC2/
make inject-textures

# --- AUDIO ---
# 3. Extraer TODAS las pistas de audio ADX a WAV y MP3 (Extracted_Audio/)
make extract-audio

# 4. Reinyectar los audios modificados de Extracted_Audio/ a MVC2/
make inject-audio

# 5. Convertir un audio individual a CRI ADX
make convert-audio INPUT=mi_tema.mp3 OUTPUT=MVC2/ADX_S000.BIN

# --- COMPILACIÓN STANDALONE ---
# 6. Compilar MvC2 a GDI (para Flycast, Redream, GDEMU)
make gdi

# 7. Compilar MvC2 a CDI (autoboot Data/Data para quemar en CD-R)
make cdi

# --- COMPILACIÓN MULTIJUEGO (CAPCOM FIGHT PACK) ---
# 8. Compilar Capcom Fight Pack 4-en-1 (MvC2 Nene + Vanilla + CvS2 + Super Turbo)
make multidisc-modular

# 9. Compilar Mini-Experimento (Menú Dricas + Super Puzzle Fighter II X)
make multidisc-mini
```

---

## 📚 Documentación y Guías

- 🕹️ **[Documentación Técnica del Motor Multidisco](file:///home/tortita/Coding/Github/Side/mvc2_custom/Docs/DREAMCAST_MULTIDISC_ENGINE.md)**: Arquitectura del generador CDI en Python puro, doble sesión Audio/Data a LBA 45000, ordenamiento BFS ISO9660, y de-duplicación por inodos.
- 📖 **[Flujo de Trabajo, Roundtrip y Compatibilidad Hardware](file:///home/tortita/Coding/Github/Side/mvc2_custom/FLUJO_ROUNDTRIP_Y_MAKEFILE.md)**: Explicación detallada del proceso de Roundtrip (Ida y Vuelta) de texturas y audio, y compatibilidad 100% con consolas Dreamcast reales.
- 💿 **[Guía de Compilación (GDI / CDI)](file:///home/tortita/Coding/Github/Side/mvc2_custom/GUIA_COMPILACION_DREAMCAST.md)**: Estructura técnica de discos de Dreamcast, configuración de `IP.BIN`, herramientas nativas y compilación paso a paso.
- 🎨 **[Guía de Modding y Herramientas](file:///home/tortita/Coding/Github/Side/mvc2_custom/GUIA_MODDING_Y_HERRAMIENTAS.md)**: Modding de música (tabla de 32 canciones ADX), paletas de personajes con PalMod, edición de escenarios y parches para `1ST_READ.BIN` con Paxtez.

---

## 📂 Estructura del Repositorio

- [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2): Archivos de datos de MvC2 Nene Edition listos para compilar (`1ST_READ.BIN`, audio ADX, sprites y modelos).
- [`Games/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Games): Módulos de juegos para compilaciones multijuego (`Frontend/`, `MVC2_Vanilla/`, `CVS2/`, `SSF2X/`, `SPF2X/`).
- [`Extracted_Textures/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures): 652 texturas extraídas en formato PNG listas para editar.
- [`Extracted_Audio/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio): 42 pistas de música extraídas en formato WAV y MP3.
- [`Tools/linux/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux): Herramientas y scripts nativos (`multidisc_manager.py`, `build_gdi.py`, `build_cdi.sh`, `export_audio.py`, `import_audio.py`, `scramble`).