# Marvel vs Capcom 2 - Custom Modding & Build Pipeline (Dreamcast)

Repositorio con los datos y herramientas completas para modding, extracción/inyección de texturas y compilación a imágenes de **SEGA Dreamcast** (**GDI** y **CDI**) en Linux y Windows.

---

## 🚀 Comandos Rápidos (Makefile)

Desde la raíz del repositorio puedes ejecutar:

```bash
# Ver todos los comandos disponibles
make help

# 1. Extraer TODAS las texturas a PNG (Extracted_Textures/)
make extract-textures

# 2. Reinyectar las texturas PNG modificadas a MVC2/
make inject-textures

# 3. Compilar el juego a GDI (para Flycast, Redream, GDEMU)
make gdi

# 4. Compilar el juego a CDI (autoboot para quemar en CD-R)
make cdi

# 5. Convertir una canción a formato CRI ADX
make convert-audio INPUT=mi_tema.mp3 OUTPUT=MVC2/ADX_S000.BIN
```

---

## 📚 Documentación y Guías

- 📖 **[Flujo de Trabajo y Makefile](file:///home/tortita/Coding/Github/Side/mvc2_custom/FLUJO_ROUNDTRIP_Y_MAKEFILE.md)**: Explicación detallada del proceso de Roundtrip (Ida y Vuelta), estructura de las 652 texturas extraídas y uso de la CLI.
- 💿 **[Guía de Compilación (GDI / CDI)](file:///home/tortita/Coding/Github/Side/mvc2_custom/GUIA_COMPILACION_DREAMCAST.md)**: Estructura técnica de discos de Dreamcast, configuración de `IP.BIN`, herramientas nativas y compilación paso a paso.
- 🎨 **[Guía de Modding y Herramientas](file:///home/tortita/Coding/Github/Side/mvc2_custom/GUIA_MODDING_Y_HERRAMIENTAS.md)**: Modding de música (tabla de 32 canciones ADX), paletas de personajes con PalMod, edición de escenarios y parches para `1ST_READ.BIN` con Paxtez.

---

## 📂 Estructura del Repositorio

- [`MVC2/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/MVC2): Archivos de datos del juego listos para compilar (`1ST_READ.BIN`, audio ADX, sprites y modelos).
- [`Extracted_Textures/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Textures): 652 texturas extraídas en formato PNG listas para editar (Escenarios, Retratos, Demos y Menús).
- [`Tools/modnao/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/modnao): Motor ModNao con la suite CLI para extracción e inyección de texturas.
- [`Tools/linux/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Tools/linux): Herramientas y scripts de compilación nativos para Linux (`build_gdi.py`, `build_cdi.sh`, `scramble`, `make_ipbin.py`).