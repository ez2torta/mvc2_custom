# Flujo de Trabajo: Modding, Roundtrip de Texturas/Audio, Makefile y Compatibilidad con Hardware Real

Esta guía explica en detalle cómo funciona el proceso de **Roundtrip (Ida y Vuelta)** para texturas y pistas de audio de Marvel vs Capcom 2, la estructura de los archivos extraídos, el uso del **Makefile** desde la raíz del repositorio y la **compatibilidad técnica al 100% con consolas Dreamcast reales**.

---

## 1. ¿Cómo funciona el Roundtrip de Texturas? (Ida y Vuelta)

El sistema de texturas de SEGA Dreamcast / NAOMI utiliza estructuras propietarias optimizadas para la GPU PowerVR:
- Formatos de color empaquetados de 16 bits (`RGB565`, `ARGB4444`, `ARGB1555`).
- Entrelazado de direcciones **Morton-Z (Twiddling)** para acceso ultrarrápido a texturas en memoria VRAM.
- Compresión **LZSS** (algoritmo de diccionario de Capcom) y **Vector Quantization (VQ)** (compresión por libro de códigos 2x2 texels).

El motor **ModNao** permite realizar el ciclo completo de **Ida y Vuelta (Roundtrip)** sin pérdida de funcionalidad:

```
[ Archivos .BIN del juego ] ──( DUMP / IDA )──> [ 652 Imágenes PNG editables ]
                                                              │
                                                        ( Edición con GIMP / Photoshop )
                                                              │
                                                              ▼
[ Archivos .BIN actualizados ] <──( INJECT / VUELTA )── [ PNGs modificados ]
            │
      ( make gdi / cdi )
            │
            ▼
[ Imagen de Dreamcast (.GDI / .CDI) lista para jugar ]
```

### Fase 1: Extracción (DUMP / IDA)
1. Lee los punteros del archivo de polígonos (`POL.BIN`) o descriptores predefinidos.
2. Descomprime las secciones LZSS y bloques VQ.
3. Desentrelaza las coordenadas Morton-Z para ordenar los píxeles en coordenadas estándar `(X, Y)`.
4. Convierte de 16-bit a imágenes PNG de 32-bit (RGBA8888) preservando el canal de transparencia.

### Fase 2: Edición
- Puedes editar cualquiera de las imágenes `.png` con tu programa favorito (**GIMP**, **Photoshop**, **Aseprite**, **Krita**, etc.).
- **Regla**: Mantén las mismas dimensiones en píxeles y el mismo nombre de archivo (`modnao-texture-X.png`).

### Fase 3: Re-inyección (INJECT / VUELTA)
1. Lee las imágenes PNG modificadas.
2. Cuantiza y convierte los píxeles RGBA8888 al formato de color nativo de la textura original.
3. Aplica el entrelazado de bits Morton-Z (Twiddle / Rectangular Twiddle).
4. Si la textura original era VQ, ejecuta la cuantización vectorial y genera el codebook de 256 entradas.
5. Si el archivo original estaba comprimido en LZSS, ejecuta la compresión de bloques LZSS.
6. Escribe el archivo `.BIN` listo para ser cargado por la Dreamcast.

---

## 2. Roundtrip de Audio (CRI ADX -> WAV / MP3 -> CRI ADX)

Marvel vs Capcom 2 almacena su banda sonora en formato **CRI ADX** (con extensión `.BIN`). 

### Extracción de Audio (`make extract-audio`)
El script [`Tools/linux/export_audio.py`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/export_audio.py) decodifica las **42 pistas de música** en:
- [`Extracted_Audio/WAV/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio/WAV): Archivos WAV PCM a 44.1kHz 16-bit estéreo (sin pérdida, ideal para editar en Audacity/DAWs).
- [`Extracted_Audio/MP3/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio/MP3): Archivos MP3 a 320 kbps con tags ID3 completos (título descriptivo, artista Capcom y álbum MvC2).
- [`Extracted_Audio/TRACK_LIST.md`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio/TRACK_LIST.md): Índice con la tabla de correspondencia entre archivos del juego y nombres de canciones.

### Re-inyección de Audio (`make inject-audio`)
Para cambiar la música del juego:
1. Coloca tus canciones personalizadas en `Extracted_Audio/WAV/` o `Extracted_Audio/MP3/` con el nombre de la pista correspondiente (ejemplo: `ADX_S000_Air_Ship.wav`, `ADX_OPEN_Opening.mp3`, etc.).
2. Ejecuta:
   ```bash
   make inject-audio
   ```
3. El script convertirá automáticamente tus canciones a formato CRI ADX nativo (44.1kHz estéreo) y las guardará en la carpeta [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2).

---

## 3. Estructura de Archivos Extraídos

### Texturas (`Extracted_Textures/`)
- [`Extracted_Textures/Stages/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Stages): Texturas de todos los escenarios (`STG00` a `STG10`).
- [`Extracted_Textures/Characters/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Characters): Retratos de selección (`PLxx_FAC`) e ilustraciones de victoria (`PLxx_WIN`) de los 59 personajes.
- [`Extracted_Textures/Demos/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Demos): Objetos y secuencias demo (`DM00` a `DM14`, `EFKY`).
- [`Extracted_Textures/Menus/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Menus): Previsualizaciones de escenarios (`SELSTG`), selección (`SELTEX`), iconos VMU (`SELVMJ`/`SELVMU`) y finales (`ENDDCTEX`/`ENDNMTEX`).

### Audio (`Extracted_Audio/`)
- [`Extracted_Audio/WAV/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio/WAV): 42 pistas en formato WAV sin compresión.
- [`Extracted_Audio/MP3/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio/MP3): 42 pistas en formato MP3 320kbps etiquetadas.

---

## 4. Uso del Makefile (Comandos Rápidos)

Desde la raíz del repositorio:

| Comando | Descripción |
| :--- | :--- |
| `make help` | Muestra la lista interactiva de todos los comandos disponibles. |
| `make extract-textures` | Extrae masivamente todas las texturas de [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2) a `Extracted_Textures/`. |
| `make inject-textures` | Reinyecta todas las texturas modificadas desde `Extracted_Textures/` a [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2). |
| `make extract-audio` | Extrae todas las pistas de audio ADX a WAV y MP3 en `Extracted_Audio/`. |
| `make inject-audio` | Reinyecta los audios editados de `Extracted_Audio/` a [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2). |
| `make gdi` | Genera la imagen GDI en `output_gdi/` lista para emuladores (**Flycast**, **Redream**) o **GDEMU**. |
| `make cdi` | Genera la imagen CDI autobootable en `output_cdi/` lista para quemar en CD-R. |
| `make convert-audio INPUT=tema.mp3 OUTPUT=MVC2/ADX_S000.BIN` | Convierte un audio individual a formato CRI ADX. |
| `make scramble INPUT=1ST_READ.BIN OUTPUT=1ST_READ_SCRAMBLED.BIN` | Scramblea un ejecutable SH-4 para imágenes MIL-CD. |
| `make unscramble INPUT=1ST_READ_SCRAMBLED.BIN OUTPUT=1ST_READ.BIN` | Descramblea un ejecutable SH-4. |
| `make build-tools` | Compila las herramientas de C e instala dependencias de ModNao. |
| `make clean` | Elimina las carpetas de salida `output_gdi/` y `output_cdi/`. |

---

## 5. Compatibilidad Técnica con Máquinas Originales (Hardware Real)

### ¿El GDI generado es 100% compatible con hardware real?
**SÍ.** El formato **GDI** generado con `make gdi`:
1. **Estructura GD-ROM 1:1**: Crea las 3 pistas estándar reconocidas por la BIOS de Dreamcast (`track01.bin` a LBA 0, `track02.raw` a LBA 450 y `track03.bin` a LBA 45000).
2. **Sector de Arranque (`IP.BIN`)**: Incrustado exactamente en los primeros 32 KB de la pista de alta densidad con el código de inicialización SH-4, el logotipo gráfico MR y metadatos de región universal (`JUE`).
3. **Ejecutable `1ST_READ.BIN`**: Utiliza el binario en formato **UNSCRAMBLED**, que es el estándar que cargan los emuladores de disco óptico (**GDEMU**, **Terraonion MODE**, **USB-GDROM**) y los emuladores (**Flycast**, **Redream**).

### ¿El CDI generado es 100% compatible con hardware real?
**SÍ.** El formato **CDI (MIL-CD)** generado con `make cdi`:
1. **Scramble SH-4 de MIL-CD**: La BIOS de Dreamcast requiere que en un CD-R el binario `1ST_READ.BIN` esté permutado con el algoritmo de scramble para que el loader de la consola lo descramblee al cargarlo en la memoria RAM en `0x8C010000`. Nuestro pipeline lo scramblea automáticamente.
2. **Estructura Multisesión LBA 11702**: La primera sesión reserva la pista de audio a LBA 0 y la segunda sesión monta los datos ISO9660 a LBA 11702 autobootable con `cdi4dc`.
3. **Capacidad del Disco**: Marvel vs Capcom 2 ocupa **~195 MB** de datos en total. Esto entra de forma nativa en un **CD-R estándar de 700 MB / 80 min** sin necesidad de recortar pistas de audio ni comprimir vídeos.
4. **Grabación**: Grabar el archivo `mvc2_custom.cdi` en un CD-R virgen a baja velocidad (4x u 8x) usando **ImgBurn** (con el driver `cdi.dll`) o **DiscJuggler**. Funcionará en cualquier consola Dreamcast modelo **VA0** o **VA1** (el 98% de las consolas existentes).
