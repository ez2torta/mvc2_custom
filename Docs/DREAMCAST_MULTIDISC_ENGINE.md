# Documentación Técnica: Motor Multidisco Dreamcast (Dricas MIL-CD Dual-Session)

## 1. Resumen del Logro y Arquitectura General

Se ha diseñado y validado un **motor independiente en Python puro** capaz de generar imágenes de disco autobootables para Sega Dreamcast (`.CDI` en formato DiscJuggler versión 3.0), sin depender de herramientas propietarias obsoletas de Windows ni parches manuales de binarios.

El sistema permite integrar:
- **Frontend Interactivo de Alta Fidelidad:** Navegador web embebido Sega Dricas (Katana OS), con renderizado HTML, fuentes personalizadas, cursor de ratón analógico y efectos de sonido en triggers L/R.
- **Micro-Lanzador Dinámico (`SG_DPLDR.BIN`):** Carga y ejecución en tiempo real de binarios `1ST_READ.BIN` de múltiples juegos comerciales o homebrew ubicados en subcarpetas arbitrarias (`TPF/`, `GAME100/`, `USA3S/`, etc.) sin modificar el ejecutable original.
- **De-duplicación Inteligente de Sectores:** Optimización por inodos/hardlinks que permite compartir hasta 300+ MB de datos idénticos entre diferentes versiones del mismo juego (ej. MvC2 Nene vs Vanilla) en el mismo disco físico.

---

## 2. Los 4 Desafíos Críticos Resueltos (Causas Raíz y Soluciones)

```
+-----------------------------------------------------------------------------------------------+
|                                    ESTRUCTURA DE PISTAS CDI                                   |
+-----------------------------------------------------------------------------------------------+
| [ PISTA 1: Audio CDDA ]          | [ GAP 150 Sectores ] | [ PISTA 2: Datos Mode 2 Form 1 ]    |
| Sectores: 0 .. 33,449            | Sectores: 33450..    | LBA: 45000 .. (Autoboot IP.BIN)     |
| Silencio: 78,839,992 bytes       | Tamaño: 350,400 B    | Sector 0: Byte Exacto 79,190,408    |
+-----------------------------------------------------------------------------------------------+
```

---

### Desafío 1: Alineación Precisa del Contenedor CDI a Byte `79,190,408` (LBA 45000)
- **El Problema:** La consola o emulador Flycast reconocía el CDI generado como un "disco de música" convencional y no booteaba el menú interactivo.
- **Causa Raíz:** En el formato MIL-CD dual-session, la BIOS de Dreamcast busca el sector `IP.BIN` en la Pista 2 exactamente a **LBA 45000**. Si la longitud de la Pista 1 de Audio y los 150 sectores de GAP no suman exactamente `79,190,408` bytes desde el inicio del archivo CDI, el cabezal óptico no encuentra la cabecera `SEGA SEGAKATANA` de arranque.
- **Solución:** Se ajustó la longitud del stream de silencio de la Pista 1 a `78,839,992` bytes exactos (`78,840,000 - 8` bytes de cabecera de chunk DJ), fijando el `IP.BIN` en el byte `79,190,408` con paridad matemática EDC/ECC Reed-Solomon en cada sector de 2336 bytes.

---

### Desafío 2: Ordenamiento Canónico de la Tabla de Rutas ISO9660 (BFS vs DFS)
- **El Problema:** El test `Hola Mundo` funcionaba impecable, pero al añadir juegos con subdirectorios (`TPF/`, `GAME100/`), el menú aparecía con gráficos corruptos y no reconocía las fuentes tipográficas.
- **Causa Raíz:** La función de recorrido de directorios `os.walk()` de Python indexa en profundidad (**Depth-First Search / DFS**). La norma ISO9660 exige estrictamente que la **Path Table (L-Path / M-Path)** esté ordenada en **Amplitud por Niveles (Breadth-First Search / BFS)**:
  1. *Nivel 1:* Directorio Raíz (`Padre: #1`).
  2. *Nivel 2:* Todos los hijos directos de la raíz contiguos y en orden ASCII estricto (`Padre: #1`).
  3. *Nivel 3:* Nietos ordenados por índice de directorio padre no-decreciente.
  Al estar desordenados, el driver de archivos de Katana saltaba a índices de sectores incorrectos al resolver `/DPFONT/` o `/XDPTEX/`.
- **Solución:** Se implementó una cola BFS en `build_shared_extent_iso` que indexa jerárquicamente todos los directorios por niveles antes de asignarles LBA.

---

### Desafío 3: Aislamiento de Subcarpetas Obsoletas de Módem Dial-up
- **El Problema:** Los triggers L/R no emitían sonido y el cursor de ratón no aparecía.
- **Causa Raíz:** Los volcados de juegos japoneses de 2001 (como *Super Puzzle Fighter II X*) contenían sus propias carpetas internas de conexión a internet de la época (`TPF/DPTEX/`, `TPF/DPWWW/`, `TPF/DPFONT/`). 
  - Esto generaba una colisión de nombres con las carpetas principales del menú en la raíz (`/XDPTEX`, `/DPFONT`, `/DPWWW`).
  - Al buscar `/xdptex/manatee.drv` (driver de audio) o `/xdptex/su_icon.pvr` (cursor de ratón), el sistema se confundía con los directorios internos del juego.
- **Solución:** Se aisló el staging de los juegos para incluir **únicamente los archivos ejecutables y assets reales del juego** (los 161 archivos de raíz como `1ST_READ.BIN`, `2_DP.BIN`, `.PVR`, `.OSB`, `.ADX`), excluyendo las subcarpetas obsoletas de módem.

---

### Desafío 4: El "Bug del Archivo de 0 Bytes" y el Desfase Físico de Sectores
- **El Problema:** El HTML cargaba texto pero todas las texturas de interfaz (`.PVR`), cursores y bancos de sonido (`.MLT`) estaban desplazadas por datos de audio ADX.
- **Causa Raíz:**
  1. Dentro de los juegos existían archivos vacíos (ej. `Games/SPF2X/SONGLIST.TXT` de **0 bytes**).
  2. Al calcular los LBAs lógicos, el planificador reservó 1 sector para el archivo de 0 bytes, pero al escribir físicamente los datos en el disco con un stream secuencial, para los archivos de 0 bytes se escribían 0 bytes sin rellenar el sector.
  3. Esto produjo un **desfase en cascada de 1 sector (2048 bytes)** en toda la ISO a partir de ese archivo. La lente de la consola leía el sector `N`, pero los datos físicos de `SU_ICON.PVR` o `XDPSOUND.MLT` estaban en `N-1`.
- **Solución:**
  - Los archivos de 0 bytes se marcaron para consumir **0 sectores físicos** (cumpliendo la norma ISO9660).
  - Se implementó **posicionamiento absoluto obligatorio (`iso_f.seek((f_lba - base_lba) * 2048)`)** para cada archivo individual antes de escribir sus datos en la ISO.

---

## 3. Estructura Canónica de la Imagen de Datos (Track 2)

| Sector Relativo | LBA | Contenido / Tipo | Descripción Técnica |
| :--- | :--- | :--- | :--- |
| **0 .. 15** | 45000 .. 45015 | `IP.BIN` (System Area) | Bootstrap inicial, firma SEGA y metadatos de consolas |
| **16** | 45016 | `PVD` | Primary Volume Descriptor (Firma `LINUX`, preparador `MKISOFS`) |
| **17** | 45017 | `VDST` | Volume Descriptor Set Terminator |
| **18** | 45018 | `Padding Zeros` | 2048 bytes vacíos (Alineación estándar de `mkisofs`) |
| **19** | 45019 | `L-Path Table` | Tabla de rutas Little-Endian ordenada por niveles (BFS) |
| **20** | 45020 | `M-Path Table` | Tabla de rutas Big-Endian ordenada por niveles (BFS) |
| **21 .. 29** | 45021 .. 45029 | `Tablas de Directorio` | `/`, `/DPETC`, `/DPFONT`, `/DPWWW`, `/XDPTEX`, `/TPF`, etc. |
| **30 ..** | 45030 .. | `Archivos Físicos` | `1ST_READ.BIN`, fuentes, texturas PVR y assets de juegos |

---

## 4. Comandos Integrados en el Makefile

Para facilitar la construcción y pruebas repetibles, el proyecto cuenta con los siguientes comandos:

```bash
# 1. Test Hola Mundo Aislado (Browser puro sin juegos - 94 MB)
make multidisc-holamundo

# 2. Test Mini-Puzzle (Frontend Dricas + Super Puzzle Fighter II X - 175 MB)
make multidisc-mini

# 3. Compilación Completa Capcom Fight Pack (5 Juegos + Soundtracks - 850 MB)
make multidisc-modular
```

---

## 5. Pruebas y Validación en Emuladores / Hardware Real

Para probar cualquier imagen resultante:
```bash
flycast output_cdi/mini_puzzle_multidisc.cdi
```
- **Controles en Menú:**
  - **Stick Analógico / Mouse:** Mueve el cursor `SU_ICON.PVR`.
  - **Cruceta (D-Pad):** Navega entre los enlaces del HTML.
  - **Botón A:** Activa el lanzador del juego seleccionado.
  - **Triggers L / R:** Reproducen efectos sonoros de clic (`XDPSOUND.MLT`).
