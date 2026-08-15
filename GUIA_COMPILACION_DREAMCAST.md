# Guía de Compilación para SEGA Dreamcast (GDI / CDI) en Linux

Esta guía detalla el estado actual del repositorio, los componentes necesarios para reconstruir el juego en formato **GDI** o **CDI**, y las herramientas disponibles en **Linux** y **Windows**.

---

## 1. Diagnóstico del Repositorio

El repositorio cuenta con los datos extraídos de **Marvel vs Capcom 2** para SEGA Dreamcast con modificaciones ya aplicadas:

- **Carpeta [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2)**:
  - Contiene todos los assets del juego (sprites, escenarios, texturas PVR, fuentes y pistas de audio ADX).
  - **`1ST_READ.BIN`**: Ejecutable principal del juego (procesador Hitachi SH-4). Actualmente se encuentra en formato **UNSCRAMBLED** (plano), parcheado con mejoras de la comunidad (All Unlocks, Rematch Mod, Random Stage Fix, Paletas de 16 colores, etc.).
- **Carpetas [`Stages/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Stages) y [`Demo/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Demo)**:
  - Texturas PNG extraídas de los escenarios y archivos binarios modificados.
- **Carpeta [`Tools/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools)**:
  - `BootDreams 1.06c`: Suite clásica de Windows para crear imágenes CDI autoejecutables.
  - `PalMod`: Editor de paletas para personajes de juegos de lucha (Windows).
  - `adx`: Encoders/decoders de audio para Windows.
  - `Tools/linux/`: Herramientas y scripts nativos para compilar en Linux.

---

## 2. Diferencia entre formatos: ¿GDI o CDI?

| Característica | **GDI (GD-ROM Image)** | **CDI (DiscJuggler / MIL-CD)** |
| :--- | :--- | :--- |
| **Capacidad** | 1.2 GB (High Density GD-ROM) | ~700 MB (CD-R estándar de 80 min) |
| **Uso principal** | Emuladores (Flycast, Redream) y Hardware Real con ODEs (GDEMU, Terraonion MODE) | Consolas Dreamcast reales originales quemando en CD-R virgen |
| **Estado de `1ST_READ.BIN`** | **UNSCRAMBLED** (sin codificar) | **SCRAMBLED** (codificado con algoritmo de permutación) |
| **Estructura** | 3 pistas: `track01.bin` (datos LD), `track02.raw` (audio), `track03.bin` (datos HD LBA 45000) + `disc.gdi` | 2 sesiones (Audio a LBA 0 + Datos ISO a LBA 11702 autobootable) |
| **Recomendación** | **Muy recomendada** (no requiere compresión ni trucos de LBA) | Solo si vas a quemar un disco físico CD-R |

---

## 3. ¿Qué herramientas faltaban y cómo se resuelven en Linux?

### A. Sector de arranque (`IP.BIN`)
- **Qué es**: Un bloque de 32 KB (16 sectores de 2048 bytes) que contiene la cabecera de Sega, el logo MR y el código de inicialización del hardware SH-4.
- **Solución implementada**: Se creó el script [`Tools/linux/make_ipbin.py`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/make_ipbin.py) para generar un `IP.BIN` personalizado con el nombre del juego (`MARVEL VS. CAPCOM 2`), bootfile (`1ST_READ.BIN`) y región universal (`JUE`).

### B. Scrambler de binarios SH-4 (`scramble`)
- **Qué es**: La BIOS de Dreamcast espera que en los discos MIL-CD (CDI) el binario `1ST_READ.BIN` tenga sus direcciones permutadas para que el loader lo desensamble en RAM en `0x8C010000`. En GDI se requiere sin permutar.
- **Solución implementada**: Se compiló la utilidad nativa [`Tools/linux/scramble`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/scramble) a partir de [`scramble.c`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/scramble.c).

### C. Generador de imágenes ISO (`genisoimage` / `mkisofs`)
- **Qué es**: Herramienta estándar de Linux para empaquetar carpetas en sistemas de archivos ISO9660 a LBA 45000 (GDI) o LBA 11702 (CDI).
- **Instalación en Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install genisoimage
  ```

### D. Conversor de Audio a CRI ADX
- En Linux **no necesitas** herramientas de Windows (`radx_encode.exe`). **FFmpeg** incluye soporte nativo para codificar a ADX:
  ```bash
  ffmpeg -i cancion.mp3 -ar 44100 -ac 2 -c:a adx ADX_S000.BIN
  ```
  También puedes usar el script automatizado:
  ```bash
  ./Tools/linux/convert_audio_adx.sh mi_cancion.mp3 MVC2/ADX_S000.BIN
  ```

---

## 4. Cómo compilar paso a paso

### Opción A: Compilar a GDI (Recomendado)

1. Instala `genisoimage` si no lo tienes:
   ```bash
   sudo apt install genisoimage
   ```
2. Ejecuta el script de construcción de GDI:
   ```bash
   python3 Tools/linux/build_gdi.py output_gdi
   ```
3. El resultado se guardará en `output_gdi/`:
   - `disc.gdi`
   - `track01.bin`
   - `track02.raw`
   - `track03.bin`
4. Carga `disc.gdi` directamente en **Flycast** o **Redream**, o copia la carpeta a tu tarjeta SD para **GDEMU**.

---

### Opción B: Compilar a CDI (Para quemar en CD-R)

1. Asegúrate de tener `genisoimage`:
   ```bash
   sudo apt install genisoimage
   ```
2. Para empaquetar el CDI final en Linux puedes usar `wine` con `cdi4dc` o la utilidad nativa:
   ```bash
   ./Tools/linux/build_cdi.sh output_cdi
   ```
3. Si prefieres hacerlo mediante entorno gráfico en Windows / Wine:
   - Abre `Tools/BootDreams-1.06c/BootDreams.exe` con Wine (`wine BootDreams.exe`).
   - Selecciona la carpeta `MVC2/`.
   - Selecciona formato **CDI (Data/Data)**.
   - Cuando pregunte si el binario ya está scrambleado, responde **No** (para que BootDreams lo scramblee automáticamente).

---

## 5. Resumen de comandos útiles en Linux

```bash
# 1. Compilar la herramienta scramble (ya compilada en Tools/linux/scramble):
gcc -O2 Tools/linux/scramble.c -o Tools/linux/scramble

# 2. Scramblear un binario para CDI:
./Tools/linux/scramble MVC2/1ST_READ.BIN 1ST_READ_SCRAMBLED.BIN

# 3. Descramblear un binario para GDI o desensamblado:
./Tools/linux/scramble 1ST_READ_SCRAMBLED.BIN 1ST_READ_UNSCRAMBLED.BIN

# 4. Convertir música a ADX con FFmpeg:
ffmpeg -i track.wav -ar 44100 -ac 2 -c:a adx MVC2/ADX_S000.BIN

# 5. Generar imagen GDI completa:
python3 Tools/linux/build_gdi.py output_gdi
```
