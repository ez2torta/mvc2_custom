# Guía de Modding y Herramientas para Marvel vs Capcom 2 (Dreamcast)

Esta guía explica cómo modificar paletas de personajes, música, escenarios y opciones del ejecutable de Marvel vs Capcom 2 en Linux y Windows.

---

## 1. Modificación de Música (Pistas ADX)

Marvel vs Capcom 2 utiliza el códec de audio **CRI ADX** (con extensión `.BIN` en el juego).
Gracias al binario parcheado incluido en este repositorio (`1st_read-2021-10-AllowNewSongs`), el juego soporta hasta **32 canciones independientes** incluyendo versiones alternativas de los escenarios.

### Tabla de Canciones del Juego

| Escenario / Pantalla | Nombre de Archivo | Escenario Alternativo | Archivo Alternativo |
| :--- | :--- | :--- | :--- |
| **Air Ship** | `ADX_S000.BIN` | Alternate Ship | `ADX_NSHP.BIN` |
| **Desert** | `ADX_S010.BIN` | Alternate Desert | `ADX_NDST.BIN` |
| **Factory** | `ADX_S020.BIN` | - | - |
| **Carnival** | `ADX_S030.BIN` | Alternate Carnival | `ADX_NCRN.BIN` |
| **Swamp** | `ADX_S040.BIN` | Alternate Swamp | `ADX_NSWP.BIN` |
| **Cave** | `ADX_S050.BIN` | Alternate Cave | `ADX_NCAV.BIN` |
| **Clock Tower** | `ADX_S060.BIN` | Alternate Clock | `ADX_NCLK.BIN` |
| **River** | `ADX_S070.BIN` | Alternate River | `ADX_NRFT.BIN` |
| **Abyss 1** | `ADX_S080.BIN` | **Abyss 2** | `ADX_S090.BIN` |
| **Abyss 3** | `ADX_S0A0.BIN` | **Training Stage** | `ADX_S0B0.BIN` |
| **Opening** | `ADX_OPEN.BIN` | **Credits** | `ADX_STAF.BIN` |
| **Capcom Logo** | `ADX_CAPL.BIN` | **Character Select** | `ADX_SELC.BIN` |
| **Continue** | `ADX_CONT.BIN` | **Here Comes Challenger** | `ADX_HERE.BIN` |
| **Game Over** | `ADX_OVER.BIN` | **Ranking** | `ADX_RANK.BIN` |
| **Win Screen** | `ADX_WINS.BIN` | **Main Menu** | `ADX_MENU.BIN` |
| **Network Menu** | `ADX_NETW.BIN` | | |

### Cómo convertir canciones en Linux con FFmpeg

No necesitas herramientas de Windows como `radx_encode.exe`. Puedes usar directamente FFmpeg:

```bash
# Convierte cualquier archivo de audio (MP3, WAV, FLAC, OGG) a ADX:
ffmpeg -i mi_tema.mp3 -ar 44100 -ac 2 -c:a adx MVC2/ADX_S000.BIN
```

O usa el script incluido:
```bash
./Tools/linux/convert_audio_adx.sh mi_tema.mp3 MVC2/ADX_S000.BIN
```

---

## 2. Modificación de Paletas y Colores (PalMod)

**PalMod** es la herramienta estándar de la comunidad para editar los colores de los trajes de los personajes y efectos de magias.

- **Ubicación en el repo**: Los archivos divididos están en [`Tools/PalMod-*.zip.*`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools).
- **En Linux**:
  1. Descomprime las partes:
     ```bash
     7z x Tools/PalMod-1.79.1603-64bit.zip.001
     ```
  2. Ejecuta PalMod con Wine:
     ```bash
     wine PalMod.exe
     ```
  3. En PalMod, selecciona `Load Directory` y apunta a la carpeta [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2).
  4. Modifica los trajes de cualquier personaje (archivos `PLxx_*.BIN`) y guarda los cambios directamente.

---

## 3. Modificación de Texturas y Modelos con ModNao (Ida y Vuelta)

En la carpeta [`Tools/modnao/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/modnao) se encuentra la herramienta de modding **ModNao**. Hemos implementado una interfaz CLI completa en Node.js/TypeScript y scripts en Bash para automatizar la extracción masiva a PNG y la re-inyección de texturas empaquetadas a los archivos `.BIN` de Dreamcast.

### A. Extraer todas las texturas del juego a PNG (DUMP)
Ejecuta el script desde la raíz del repositorio:
```bash
./Tools/linux/export_textures.sh
```
O directamente con NPM / TSX en ModNao:
```bash
cd Tools/modnao
npm run textures:dump
```
Esto creará la carpeta `Extracted_Textures/` organizada por categorías:
- `Stages/`: Texturas de todos los escenarios (`STG00` a `STG10`).
- `Characters/`: Retratos de selección (`PLxx_FAC`) y retratos de victoria (`PLxx_WIN`) de los 59 personajes.
- `Demos/`: Modelos y texturas de secuencias/demos (`DM00` a `DM14`, `EFKY`).
- `Menus/`: Selección de escenario (`SELSTG`), selección de personajes (`SELTEX`), VMU (`SELVMJ`/`SELVMU`) y finales (`ENDDCTEX`, `ENDNMTEX`).

### B. Editar las texturas
- Abre cualquier imagen `modnao-texture-X.png` con tu editor favorito (**GIMP**, **Photoshop**, **Aseprite**, etc.).
- Modifica los gráficos manteniendo las dimensiones originales en píxeles.
- Guarda el archivo `.png` en la misma ubicación.

### C. Reinyectar las texturas modificadas a los archivos .BIN (INJECT)
Para empaquetar de vuelta los PNGs editados a los archivos `.BIN` del juego:
```bash
./Tools/linux/import_textures.sh
```
O con NPM:
```bash
cd Tools/modnao
npm run textures:inject
```
El motor de ModNao se encarga automáticamente de:
- Codificar las imágenes al formato de color nativo de Dreamcast (`RGB565`, `ARGB4444`, `ARGB1555`).
- Aplicar el entrelazado de direcciones Morton Z (Twiddle y Rectangular Twiddle).
- Comprimir con **Vector Quantization (VQ)** y **LZSS** según corresponda para cada archivo.

### D. Comandos individuales por archivo
Si solo deseas extraer o inyectar un escenario o personaje específico:
```bash
cd Tools/modnao

# Extraer un escenario específico (POL + TEX):
npx tsx src/cli/index.ts dump-file ../../MVC2/STG00TEX.BIN ../../Stages/STG00TEX ../../MVC2/STG00POL.BIN

# Reinyectar un escenario específico:
npx tsx src/cli/index.ts inject-file ../../MVC2/STG00TEX.BIN ../../Stages/STG00TEX ../../MVC2/STG00TEX.BIN ../../MVC2/STG00POL.BIN

# Extraer el retrato de Ryu:
npx tsx src/cli/index.ts dump-file ../../MVC2/PL00_FAC.BIN /tmp/ryu_fac

# Reinyectar el retrato de Ryu:
npx tsx src/cli/index.ts inject-file ../../MVC2/PL00_FAC.BIN /tmp/ryu_fac ../../MVC2/PL00_FAC.BIN
```

---

## 4. Personalización del Ejecutable (`1ST_READ.BIN`) con Paxtez

Para generar binarios personalizados con opciones avanzadas de jugabilidad:

- Visita la herramienta web oficial de la comunidad: [https://paxtez.zachd.com/](https://paxtez.zachd.com/)
- Opciones configurables:
  - **Desbloqueos completos** sin necesidad de tarjeta VMU.
  - **Random Stage Fix**: Arregla el bug del juego original que impedía que salieran ciertos escenarios en modo aleatorio.
  - **Rematch Mod**: Permite reiniciar la pelea inmediatamente pulsando Start.
  - **Paletas expandidas** (soporte para 16 botones/combinaciones de colores).
  - **Reorganización del Character Select**: Ordenado por tiers competitivos o layout clásico.
  - **Desactivar Handicap**: Para juego competitivo justo.
- Una vez generado tu `1ST_READ.BIN` desde la web, simplemente reemplaza el archivo [`MVC2/1ST_READ.BIN`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2/1ST_READ.BIN) y vuelve a compilar la imagen GDI o CDI.
