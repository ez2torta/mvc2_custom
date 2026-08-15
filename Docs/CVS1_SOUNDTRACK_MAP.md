# 🎵 Guía de Mapeo y Audición de Bandas Sonoras: Capcom vs. SNK 1

Esta herramienta te permite audicionar en formato MP3 todas las pistas de audio originales de **Capcom vs. SNK: Millennium Fight 2000**, y configurar manualmente qué tema de los otros juegos (MvC2, CvS2, Super Turbo, 3rd Strike, Puzzle Fighter) sonará en cada escenario, intro, menú o jingle de CvS1.

---

## 🎧 1. Cómo Escuchar las Pistas en tu Computador

Todas las 48 pistas de audio de CvS1 han sido convertidas a formato MP3 con nombres descriptivos en la carpeta:

📂 **[`Extracted_Audio/CVS1_MP3/`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Extracted_Audio/CVS1_MP3)**

Puedes abrirlas con cualquier reproductor (VLC, reproductor de música, navegador) para escuchar exactamente qué melodía suena en cada archivo.

---

## ✍️ 2. Cómo Modificar el Mapeo Manualmente

1. Abre el archivo de configuración editable:
   📄 **[`Docs/CVS1_SOUNDTRACK_MAP.json`](file:///home/tortita/Coding/Github/Side/mvc2_custom/Docs/CVS1_SOUNDTRACK_MAP.json)**

2. Cada pista tiene esta estructura:
   ```json
   "ADX_1700.BIN": {
     "role": "Opening Demo & Title",
     "type": "intro",
     "desc": "Intro del juego y pantalla de inicio (Press Start)",
     "targets": {
       "CVS2": "ADX_OPEN.BIN",
       "MVC2": "ADX_OPEN.BIN",
       "3S": "52_OPEN.ADX",
       "ST": "DEMO_33.ADX",
       "PF": "Q0C_OPEN.ADX",
       "FANDISK": "ADX_OPEN.BIN"
     }
   }
   ```

3. Simplemente cambia el nombre del archivo en `targets` por la pista que quieras que suene para esa versión de banda sonora.

---

## ⚡ 3. Aplicar los Cambios al Motor Multijuego

Cuando termines de editar el archivo JSON, ejecuta en tu terminal:

```bash
# 1. Aplicar los cambios al motor de audio
python3 Tools/linux/cvs1_soundtrack_mapper.py apply

# 2. Recompilar el CDI multijuego con el nuevo mapeo
make multidisc
```

---

## 📋 4. Comandos de la Herramienta CLI

```bash
# Ver la tabla completa en consola
python3 Tools/linux/cvs1_soundtrack_mapper.py list

# Re-exportar las canciones a MP3
python3 Tools/linux/cvs1_soundtrack_mapper.py export-audio

# Aplicar las modificaciones del JSON al compilador
python3 Tools/linux/cvs1_soundtrack_mapper.py apply
```
