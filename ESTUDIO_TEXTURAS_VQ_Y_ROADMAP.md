# Estudio Técnico: Texturas VQ (Vector Quantization), Mipmaps y Hoja de Ruta en ModNao

Este documento analiza en detalle el estado de las texturas con compresión **VQ (Vector Quantization)** y **Mipmaps** en Marvel vs Capcom 2 (Dreamcast), identifica exactamente qué archivos las utilizan y define los pasos técnicos para iterar y completarlas al 100%.

---

## 1. ¿Qué es la Compresión VQ en SEGA Dreamcast (PowerVR)?

La GPU PowerVR Series 2 (CLX2) de la Dreamcast incorpora descompresión por hardware de **Vector Quantization (VQ)**:
- La imagen se divide en bloques (vectores) de **2x2 texels** (4 píxeles).
- En lugar de guardar los 4 píxeles (8 bytes en RGB565), se crea un **Codebook (paleta de vectores)** con las **256 combinaciones de 2x2 píxeles más representativas** (`256 × 8 bytes = 2048 bytes`).
- El cuerpo de la imagen se almacena como un mapa de índices de **1 byte por cada bloque de 2x2 píxeles** (`(Ancho × Alto) / 4` bytes).
- **Ratio de compresión**: Reduce el peso de las texturas en una proporción de **8 a 1** con respecto a los datos sin comprimir.

---

## 2. Escaneo Completo de Tipos de Texturas en Marvel vs Capcom 2

Tras escanear todos los descriptores de polígonos (`POL.BIN`) del juego, esta es la distribución exacta:

| Tipo (`Type Code`) | Descripción | Cantidad en MvC2 | Estado en ModNao |
| :--- | :--- | :---: | :--- |
| **`Type 1`** | Twiddled Cuadrado Estándar | **319** | **100% Soportado** (Escenarios, Personajes, Menús) |
| **`Type 13`** | Rectangular Twiddled | **10** | **100% Soportado** (Fuentes y paneles) |
| **`Type 3`** | Vector Quantized (VQ) | **48** (+ 118 en retratos) | **Soportado con limitaciones** (Demos, Efectos, Retratos) |
| **`Type 2`** | Twiddled + Mipmaps | **5** | **Parcial / Pendiente** (Desfase de lectura de mipmaps) |
| **`Type 4`** | VQ + Mipmaps | **0 en MvC2** (Común en CvS2) | **No implementado** en ModNao |

---

## 3. Archivos Específicos que Utilizan VQ y Mipmaps

### A. Efectos Especiales (`EFKYPOL.BIN` + `EFKYTEX.BIN`)
- **25 texturas en formato VQ (`Type 3`)**:
  - Texturas 0 a 18: 128x128 y 256x256 en `ARGB4444` y `RGB565`.
  - Texturas 19 a 24: 256x256 en formato `ARGB1555`.

### B. Demos e Introducciones (`DMxxPOL.BIN` + `DMxxTEX.BIN`)
- **`DM00TEX.BIN`**: Textura 9 (256x256 RGB565 VQ), Texturas 22, 23, 24 (128x128 RGB565 VQ).
- **`DM01TEX.BIN`**: Texturas 12, 13 (256x256 ARGB1555 VQ).
- **`DM02TEX.BIN`**: Texturas 2 a 7 (128x128 RGB565 VQ).
- **`DM0CTEX.BIN`**: Textura 4 (128x128 RGB565 VQ).
- **`DM0DTEX.BIN`**: Texturas 8, 9, 12, 13, 14, 15, 17, 19, 21 (64x64 y 256x256 ARGB4444 VQ).
- **`DM0FTEX.BIN`**: Textura 5 (512x512 ARGB4444 VQ).

### C. Retratos de Selección de Personajes (`PLxx_FAC.BIN`)
- Los **59 personajes** (`PL00_FAC` a `PL3A_FAC`) utilizan VQ en:
  - Textura 1 (256x256): Retrato Super Combo / Hyper portrait.
  - Textura 2 (128x128): Retrato VS / Selection.

### D. Archivos con Mipmaps (`Type 2`)
- **`DM05TEX.BIN`**: Texturas 1 (128x128) y 2 (256x256).
- **`DM07TEX.BIN`**: Texturas 3 (128x128) y 4 (256x256).
- **`DM08TEX.BIN`**: Textura 5 (128x128).

---

## 4. Diagnóstico de los Problemas en ModNao

1. **Problema de Mipmaps (`Type 2` y `Type 4`)**:
   - En una textura con mipmaps, el archivo contiene primero las sub-imágenes reducidas (`1×1, 2×2, 4×4 ... (W/2)×(H/2)`) antes de la imagen principal.
   - El tamaño de todos los mipmaps previos equivale exactamente a `(Ancho × Alto × 2) / 3` bytes.
   - ModNao lee desde el byte 0 asumiendo que no hay mipmaps, provocando que la imagen se vea corrida/corrupta.

2. **Problema de "Small VQ" o VQ con Codebook Parcial**:
   - En texturas pequeñas (ej. 64x64 en `DM0DPOL.BIN`), el codebook puede ser reducido o compartir vectores en VRAM.
   - ModNao asume siempre un codebook completo de 2048 bytes.

3. **Rendimiento de Compresión VQ en JavaScript (K-Means)**:
   - ModNao utiliza la librería `ml-kmeans` en Node/JS para agrupar vectores en 256 clusters.
   - Generar un codebook VQ en JS tarda ~7 segundos por imagen. Reinyectar 59 retratos toma ~7 minutos.

---

## 5. Hoja de Ruta para Iterar y Resolver VQ / Mipmaps

```
[ Fase 1: Soporte de Mipmaps ] ──> [ Fase 2: Soporte ARGB1555 VQ ] ──> [ Fase 3: Encoder VQ Nativo en C/Wasm ]
```

### Paso 1: Implementar el Parser de Mipmaps (`Type 2` y `Type 4`)
Calcular el offset de cabecera de mipmaps en `loadTextureFileWorker.ts`:
```ts
function getMipmapByteOffset(width: number, height: number, isVq: boolean): number {
  if (!isVq) {
    // Suma de 1x1 + 2x2 + ... + (w/2 x h/2) en 16-bit
    return Math.floor((width * height * 2) / 3);
  } else {
    // En VQ los mipmaps previos son índices de 1 byte por bloque 2x2
    return Math.floor((width * height) / 12);
  }
}
```

### Paso 2: Optimizar `ARGB1555` en `compressVqBuffer.ts`
Completar la tabla de distancias de color Euclidianas para `ARGB1555` con canal de corte alfa binario (1-bit: 0 o 255) para que `DM01TEX.BIN` y `EFKYTEX.BIN` codifiquen con máxima nitidez.

### Paso 3: Acelerador VQ Nativo en C (Algoritmo LBG / Linde-Buzo-Gray)
Escribir un pequeño ejecutable o módulo en C (`Tools/linux/vq_encode.c`) usando el algoritmo clásico LBG para Vector Quantization de PowerVR:
- Reduce el tiempo de compresión de **7 segundos a 15 milisegundos por textura**.
- Permite reinyectar el juego completo en menos de 2 segundos.
