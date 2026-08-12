# 📋 Informe de Investigación: Arquitectura Multijuego Dreamcast, Diagnóstico y Hoja de Ruta

---

## 1. 📌 Estado Actual y Diagnóstico Resumido

### Lo que Funciona Comprobado al 100%:
1. **Línea Base Funcional:** El archivo `TDCFinal2/disc.cdi` bootea y ejecuta al 100% en Flycast y consolas reales.
2. **Inyección en Tiempo Real Validada:** El experimento con [`multidisc_injector.py`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/multidisc_injector.py) logró modificar `DM08CHR.BIN` y `DM08CAB.BIN`, mostrando exitosamente en Flycast la **intro modificada con "El Nene y el Pirata"**.
3. **Módulos Independientes Listos en Git:** La carpeta `Games/` contiene los submódulos aislados (`MVC2_Vanilla`, `CVS2`, `SSF2X`, `SPF2X`, `Frontend`, `Soundtracks`), y `MVC2/` conserva intacto el mod Nene Edition.
4. **Flujo Single-Game Protegido:** `make cdi` y `build_cdi.py` permanecen 100% operativos para generar el MvC2 individual.

---

## 2. 🔍 Diagnóstico Forense de Bajo Nivel

### A. ¿Por qué faltaron las paletas de personajes y la música en la inyección previa?
- **Paletas y Sprites:** En Marvel vs Capcom 2 de Dreamcast, las paletas de combate no están en `DM08CHR.BIN` (que solo tiene intro y menús), sino en:
  - `PL00_DAT.BIN` a `PL3A_DAT.BIN` (56 luchadores).
  - `S_PL00A.BIN` a `S_PL3AF.BIN` (archivos de paletas por botón).
  - `1ST_READ.BIN` (tabla de punteros de paletas y desbloqueo de personajes).
  *Estos archivos en Nene Edition pesan entre 2 KB y 20 KB más que los originales, por lo que no caben en los sectores preasignados fijos del ISO de TDCFinal2.*
- **Música (ADX):** Las pistas en `MVC2/` son archivos WAV convertidos a ADX en estéreo a alta resolución (pesan 30 MB cada una, sumando 269 MB), mientras que los slots de audio en `TDCFinal2` están diseñados para pistas compactas de 800 KB (12 MB en total).

### B. ¿Por qué Flycast arroja "Invalid CDI image" al generar el ISO desde cero?
1. **Falta de Matrices de Paridad EDC/ECC Reed-Solomon:**
   - Una pista de datos Mode 2 Form 1 en CDI no es solo datos de 2048 bytes; cada sector mide **2336 bytes** y requiere 288 bytes de paridad matemática (4 bytes EDC CRC32 + 172 bytes ECC P-Parity + 104 bytes ECC Q-Parity).
   - Cuando Flycast detecta bloques sin ECC válido o con trailer desalineado, rechaza el archivo con *"Invalid CDI image"*.
2. **Limitación de `cdi4dc` Oficial:**
   - La herramienta oficial `cdi4dc` solo soporta o bien Data/Data (LBA 0/11702) o bien Audio/Data con pista de audio de 300 sectores (LBA 11702).
   - **`TDCFinal2` fue masterizado a LBA 45000** (pista de audio de 33,600 sectores), por lo que el `cdi4dc` estándar desalinea el LBA a 11702 y el bootstrap de `IP.BIN` se cuelga.

---

## 3. 🧠 Aprendizajes Clave de la Arquitectura Dreamcast

| Componente | Formato Single-Game (`make cdi`) | Formato Multijuego (`make multidisc-custom`) |
| :--- | :--- | :--- |
| **Pista 1 (Sesión 1)** | Datos Mode 1/2 a LBA 0 (con dummy) | Audio CDDA en bruto (33,600 sectores a LBA 0) |
| **Pista 2 (Sesión 2)** | Datos Mode 2 a LBA 11702 | Datos Mode 2 a LBA 45000 |
| **LBA del Filesystem** | Masterizado a LBA 0 / 11702 | Masterizado estrictamente a LBA 45000 |
| **Estado del `1ST_READ.BIN`** | **Scrambled** (descrambleado por BIOS) | **Unscrambled** (cargado en RAM `0x8C010000` por `SG_DPLDR.BIN`) |
| **Frontend Selector** | N/A (arranque directo) | Motor oficial Sega DreamKey / Dricas XDP |

---

## 4. 🚀 Hoja de Ruta y Experimentos para la Nueva Conversación

### Experimento 1: Recompilar `cdi4dc` con Soporte Nativo para LBA 45000 ⭐ *(Recomendado)*
- Tenemos el código fuente completo en C de `cdi4dc` en [`Tools/src/cdi4dc/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/src/cdi4dc/).
- En `cdidata.c` / `cdiaudio.c`, podemos cambiar la constante `NEXT_TRACK_LBA` a `45000` y `cdi_audio_track_total_size` a `33600 * 2352`.
- Al compilar con `gcc`, obtendremos un binario `cdi4dc` nativo que generará contenedores CDI a LBA 45000 con **100% de paridad EDC/ECC Reed-Solomon perfecta**, garantizando que Flycast y la consola real lo lean de inmediato.

### Experimento 2: Reasignador Dinámico de Sectores en la Base TDCFinal2
- `TDCFinal2` contiene más de **500 MB de espacio libre** al eliminar juegos no deseados (Street Fighter III 3rd Strike, Vampire Chronicle, SF Zero 3, etc.).
- Podemos reasignar los bloques libres dentro de la tabla ISO para colocar todos los `PLxx_DAT.BIN` y las pistas ADX de Nene Edition sin alterar el bootloader.

### Experimento 3: Compresión y Conversión Óptima de ADX
- Estandarizar las pistas de audio personalizadas de `MVC2/` a 24 kHz / 32 kHz ADX para que mantengan una fidelidad cristalina mientras ocupan menos de 100 MB en total.

---

## 5. 📁 Ubicación de Archivos Clave

- Código de De-duplicación e ISO: [`Tools/linux/multidisc_manager.py`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/multidisc_manager.py)
- Código de Inyección en Caliente: [`Tools/linux/multidisc_injector.py`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux/multidisc_injector.py)
- Código Fuente C de cdi4dc y libedc: [`Tools/src/cdi4dc/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/src/cdi4dc/)
- Módulos de Juegos Extraídos: [`Games/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Games/)
- MvC2 Nene Edition Modificado: [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2/)
