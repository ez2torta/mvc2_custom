# Flujo de Trabajo: Modding, Roundtrip de Texturas y Makefile

Esta guía explica en detalle cómo funciona el proceso de **Roundtrip (Ida y Vuelta)** de texturas para Marvel vs Capcom 2, la estructura de los archivos extraídos y cómo usar el **Makefile** desde la raíz del repositorio.

---

## 1. ¿Cómo funciona el Roundtrip? (Ida y Vuelta)

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

## 2. Estructura de Texturas Extraídas (`Extracted_Textures/`)

Se han extraído **652 texturas PNG** en 158 carpetas organizadas por categorías:

- [`Extracted_Textures/Stages/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Stages):
  - `STG00TEX` a `STG10TEX`: Texturas de todos los escenarios (barco volador, desierto, fábrica, carnaval, pantano, cueva, torre del reloj, río helado, abyss, etc.).
- [`Extracted_Textures/Characters/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Characters):
  - `PL00_FAC` a `PL3A_FAC`: Retratos de selección y barras de vida de los 59 personajes.
  - `PL00_WIN` a `PL3A_WIN`: Ilustraciones de pantalla de victoria de los 59 personajes.
- [`Extracted_Textures/Demos/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Demos):
  - `DM00TEX` a `DM14TEX`, `EFKYTEX`: Gráficos de introducciones, objetos 3D y efectos especiales.
- [`Extracted_Textures/Menus/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Menus):
  - `SELSTG`: Previsualizaciones de escenarios en la pantalla de selección.
  - `SELTEX`: Elementos de la pantalla de selección de personajes.
  - `SELVMJ` / `SELVMU`: Iconos de pantalla para Visual Memory Unit (VMU).
  - `ENDDCTEX` / `ENDNMTEX`: Ilustraciones de la secuencia de créditos finales.

---

## 3. Uso del Makefile (Comandos Rápidos)

Desde la raíz del repositorio puedes ejecutar todos los pasos cómodamente:

| Comando | Descripción |
| :--- | :--- |
| `make help` | Muestra la lista interactiva de todos los comandos disponibles. |
| `make extract-textures` | Extrae masivamente todas las texturas de [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2) a `Extracted_Textures/`. |
| `make inject-textures` | Reinyecta todas las texturas modificadas desde `Extracted_Textures/` a [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2). |
| `make gdi` | Genera la imagen GDI en `output_gdi/` lista para emuladores (**Flycast**, **Redream**) o **GDEMU**. |
| `make cdi` | Genera la imagen CDI autobootable en `output_cdi/` lista para quemar en CD-R. |
| `make convert-audio INPUT=tema.mp3 OUTPUT=MVC2/ADX_S000.BIN` | Convierte cualquier archivo de audio a formato CRI ADX. |
| `make scramble INPUT=1ST_READ.BIN OUTPUT=1ST_READ_SCRAMBLED.BIN` | Scramblea un ejecutable SH-4 para imágenes MIL-CD. |
| `make unscramble INPUT=1ST_READ_SCRAMBLED.BIN OUTPUT=1ST_READ.BIN` | Descramblea un ejecutable SH-4. |
| `make build-tools` | Compila las herramientas de C e instala dependencias de ModNao. |
| `make clean` | Elimina las carpetas de salida `output_gdi/` y `output_cdi/`. |

---

## 4. Ejemplo Práctico: Modificar un Escenario y Compilar

1. **Editar textura**:
   - Abre [`Extracted_Textures/Stages/STG00TEX/modnao-texture-2.png`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures/Stages/STG00TEX) con tu editor gráfico.
   - Realiza tus cambios y guarda el archivo PNG.

2. **Reinyectar la textura al juego**:
   ```bash
   make inject-textures
   ```

3. **Compilar a GDI**:
   ```bash
   make gdi
   ```

4. **Probar**:
   - Carga el archivo `output_gdi/disc.gdi` en tu emulador favorito (Flycast o Redream).
