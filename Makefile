# ==============================================================================
# Makefile - Marvel vs Capcom 2 (Dreamcast) Modding & Build Pipeline
# ==============================================================================

SHELL := /bin/bash
ROOT_DIR := $(shell pwd)
TOOLS_LINUX := $(ROOT_DIR)/Tools/linux
MODNAO_DIR := $(ROOT_DIR)/Tools/modnao
MVC2_DATA := $(ROOT_DIR)/MVC2
TEXTURES_DIR := $(ROOT_DIR)/Extracted_Textures
AUDIO_DIR := $(ROOT_DIR)/Extracted_Audio
OUTPUT_GDI := $(ROOT_DIR)/output_gdi
OUTPUT_CDI := $(ROOT_DIR)/output_cdi

.PHONY: all help build-tools extract-textures dump-textures inject-textures pack-textures extract-audio dump-audio inject-audio pack-audio gdi cdi cdi-dummy multidisc-custom multidisc-extract multidisc-build convert-audio scramble unscramble clean

all: help

### help: Muestra este mensaje de ayuda
help:
	@echo "========================================================================"
	@echo "    Marvel vs Capcom 2 (Dreamcast) - Modding & Build Pipeline"
	@echo "========================================================================"
	@echo "Comandos disponibles:"
	@echo ""
	@echo "  --- TEXTURAS (ModNao Engine) ---"
	@echo "  make extract-textures   Extrae texturas a PNG (Extracted_Textures/)"
	@echo "                          Opcional: ONLY=DM08CAB o FILES=DM08CAB,DM08CHR"
	@echo "  make inject-textures    Reinyecta texturas PNG editadas a MVC2/"
	@echo "                          Opcional: ONLY=DM08CAB o FILES=DM08CAB,DM08CHR"
	@echo ""
	@echo "  --- AUDIO (CRI ADX / WAV / MP3) ---"
	@echo "  make extract-audio      Extrae pistas ADX a WAV y MP3 (Extracted_Audio/)"
	@echo "                          Opcional: ONLY=ADX_S080 o TRACKS=ADX_S080,ADX_MENU"
	@echo "  make inject-audio       Reinyecta audios de Extracted_Audio/ a MVC2/"
	@echo "                          Opcional: ONLY=ADX_S080 o TRACKS=ADX_S080,ADX_MENU"
	@echo "  make convert-audio      Convierte un audio individual a CRI ADX"
	@echo "                          Uso: make convert-audio INPUT=tema.mp3 OUTPUT=MVC2/ADX_S000.BIN"
	@echo ""
	@echo "  --- COMPILACIÓN DE IMÁGENES ---"
	@echo "  make gdi                Genera la imagen GDI para emuladores/GDEMU (output_gdi/)"
	@echo "  make cdi                Genera la imagen CDI autoboot compacta (~498 MB)"
	@echo "  make cdi-dummy          Genera la imagen CDI optimizada con 0DUMMY.DAT (hasta 650 MB para CD-R)"
	@echo "  make multidisc-custom   Construye el Capcom Fight Pack curado (MvC2 Nene, Original, CvS2, SSF2X, SPF2X)"
	@echo "  make multidisc-build    Construye un CDI multijuego con de-duplicación (Uso: make multidisc-build [IN=...])"
	@echo "  make multidisc-extract  Extrae un CDI multijuego con hardlinks (Uso: make multidisc-extract [CDI=...])"
	@echo ""
	@echo "  --- HERRAMIENTAS SH-4 ---"
	@echo "  make scramble           Scramblea un binario SH-4 (Uso: make scramble INPUT=... OUTPUT=...)"
	@echo "  make unscramble         Descramblea un binario SH-4 (Uso: make unscramble INPUT=... OUTPUT=...)"
	@echo "  make build-tools        Compila herramientas nativas e instala dependencias de ModNao"
	@echo "  make clean              Limpia imágenes generadas y archivos temporales"
	@echo "========================================================================"

## build-tools: Compila binarios nativos (scramble, cdi4dc) e instala dependencias de Python y ModNao
build-tools:
	@echo "[*] Compilando herramienta scramble en C..."
	gcc -O2 $(TOOLS_LINUX)/scramble.c -o $(TOOLS_LINUX)/scramble
	@echo "[*] Compilando herramienta cdi4dc en C..."
	gcc -O2 -I$(ROOT_DIR)/Tools/src/cdi4dc/common/inc -I$(ROOT_DIR)/Tools/src/cdi4dc/edc/inc -I$(ROOT_DIR)/Tools/src/cdi4dc/cdi4dc/inc \
		$(ROOT_DIR)/Tools/src/cdi4dc/cdi4dc/src/*.c $(ROOT_DIR)/Tools/src/cdi4dc/common/src/*.c $(ROOT_DIR)/Tools/src/cdi4dc/edc/src/*.c \
		-o $(TOOLS_LINUX)/cdi4dc
	@echo "[*] Verificando dependencias de Python (pycdlib)..."
	python3 -m pip install -r $(ROOT_DIR)/requirements.txt --break-system-packages --quiet 2>/dev/null || python3 -m pip install -r $(ROOT_DIR)/requirements.txt --quiet || true
	@echo "[*] Verificando dependencias de ModNao..."
	cd $(MODNAO_DIR) && npm install --silent
	@echo "[✓] Todas las herramientas y dependencias listas."

## extract-textures / dump-textures: Extrae texturas de MVC2 a PNG (Opcional: ONLY=... o FILES=...)
extract-textures: dump-textures
dump-textures:
	@echo "[*] Extrayendo texturas con ModNao..."
	$(TOOLS_LINUX)/export_textures.sh "$(MVC2_DATA)" "$(TEXTURES_DIR)" "$(ONLY)$(FILES)$(NAMES)"

## inject-textures / pack-textures: Reinyecta texturas editadas a los .BIN (Opcional: ONLY=... o FILES=...)
inject-textures: pack-textures
pack-textures:
	@echo "[*] Reinyectando texturas modificadas a MVC2/..."
	$(TOOLS_LINUX)/import_textures.sh "$(TEXTURES_DIR)" "$(MVC2_DATA)" "$(MVC2_DATA)" "$(ONLY)$(FILES)$(NAMES)"

## extract-audio / dump-audio: Extrae pistas de audio ADX a WAV y MP3 (Opcional: ONLY=... o TRACKS=...)
extract-audio: dump-audio
dump-audio:
	@echo "[*] Extrayendo pistas de audio ADX a WAV y MP3..."
	python3 $(TOOLS_LINUX)/export_audio.py "$(MVC2_DATA)" "$(AUDIO_DIR)" "$(ONLY)$(TRACKS)$(FILES)$(NAMES)"

## inject-audio / pack-audio: Reinyecta WAV/MP3 a ADX en MVC2/ (Opcional: ONLY=... o TRACKS=...)
inject-audio: pack-audio
pack-audio:
	@echo "[*] Reinyectando pistas de audio a formato CRI ADX en MVC2/..."
	python3 $(TOOLS_LINUX)/import_audio.py "$(AUDIO_DIR)" "$(MVC2_DATA)" "$(ONLY)$(TRACKS)$(FILES)$(NAMES)"

## gdi: Genera la imagen GDI completa (disc.gdi, track01, track02, track03)
gdi:
	@echo "[*] Generando imagen GDI..."
	python3 $(TOOLS_LINUX)/build_gdi.py "$(OUTPUT_GDI)"

## cdi: Genera la imagen CDI autobootable (Sin dummy ~498MB, o con DUMMY=650)
cdi:
	@echo "[*] Generando imagen CDI..."
	$(TOOLS_LINUX)/build_cdi.sh "$(OUTPUT_CDI)" "$(DUMMY)"

## cdi-dummy: Genera la imagen CDI autobootable optimizada con 0DUMMY.DAT (hasta 650 MB para CD-R)
cdi-dummy:
	@echo "[*] Generando imagen CDI optimizada con 0DUMMY.DAT (hasta 650 MB)..."
	$(TOOLS_LINUX)/build_cdi.sh "$(OUTPUT_CDI)" "650"

## multidisc-custom: Inyecta MvC2 Nene Edition y menús personalizados en el multijuegos compatible
multidisc-custom:
	@echo "[*] Inyectando MvC2 Nene Edition en compilación multijuego..."
	python3 $(TOOLS_LINUX)/multidisc_injector.py "$(OUTPUT_CDI)/mvc2_nene_multidisc.cdi"

## multidisc-inject: Alias de multidisc-custom
multidisc-inject: multidisc-custom

## multidisc-extract: Extrae un CDI multijuego preservando hardlinks
multidisc-extract:
	@echo "[*] Extrayendo CDI multijuego con hardlinks..."
	python3 $(TOOLS_LINUX)/multidisc_manager.py extract --input "$${CDI:-$(ROOT_DIR)/TDCFinal2/disc.cdi}" --output "$${OUT:-$(ROOT_DIR)/MultiGames/TDC_Extracted}"

## multidisc-build: Construye un CDI multijuego con de-duplicación de sectores
multidisc-build:
	@echo "[*] Construyendo CDI multijuego / multi-soundtrack..."
	python3 $(TOOLS_LINUX)/multidisc_manager.py build --input "$${IN:-$(ROOT_DIR)/MultiGames/TDC_Extracted}" --output "$${OUT:-$(OUTPUT_CDI)/multidisc_custom.cdi}" --volume "$${VOL:-MULTIDISC}"

## convert-audio: Convierte audio individual a ADX
convert-audio:
	@if [ -z "$(INPUT)" ]; then \
		echo "[!] Error: Especifica INPUT=<archivo_audio> [OUTPUT=<archivo_adx>]"; \
		exit 1; \
	fi
	$(TOOLS_LINUX)/convert_audio_adx.sh "$(INPUT)" "$(OUTPUT)"

## scramble: Permuta bits de direcciones para MIL-CD
scramble:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "[!] Error: Uso: make scramble INPUT=<archivo_in> OUTPUT=<archivo_out>"; \
		exit 1; \
	fi
	$(TOOLS_LINUX)/scramble "$(INPUT)" "$(OUTPUT)"

## unscramble: Despermuta bits de direcciones
unscramble:
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "[!] Error: Uso: make unscramble INPUT=<archivo_in> OUTPUT=<archivo_out>"; \
		exit 1; \
	fi
	$(TOOLS_LINUX)/scramble "$(INPUT)" "$(OUTPUT)"

## clean: Limpia directorios de salida
clean:
	@echo "[*] Limpiando directorios de compilación..."
	rm -rf "$(OUTPUT_GDI)" "$(OUTPUT_CDI)"
	@echo "[✓] Limpieza completada."
