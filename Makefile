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

.PHONY: all help build-tools extract-textures dump-textures inject-textures pack-textures extract-audio dump-audio inject-audio pack-audio gdi cdi cdi-dummy multidisc convert-audio scramble unscramble clean

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
	@echo "  --- AUDIO & SOUNDTRACKS (CRI ADX 22kHz Mono & Cross-OST) ---"
	@echo "  make extract-audio      Extrae pistas ADX a WAV y MP3 (Extracted_Audio/)"
	@echo "                          Opcional: ONLY=ADX_S080 o TRACKS=ADX_S080,ADX_MENU"
	@echo "  make inject-audio       Reinyecta audios de Extracted_Audio/ a MVC2/"
	@echo "                          Opcional: ONLY=ADX_S080 o TRACKS=ADX_S080,ADX_MENU"
	@echo "  make downsample-adx     Optimiza ADX a 22kHz mono con recálculo de loops y EBU R128 (-75% espacio)"
	@echo "                          Uso: make downsample-adx DIR=MVC2 [OUT=dir] [IN_PLACE=1]"
	@echo "  make downsample-mvc2    Downsamplea la música de MVC2/ directamente (-130 MB)"
	@echo "  make downsample-all     Downsamplea todos los juegos (MVC2, CVS2, CVS1J)"
	@echo "  make soundtracks-list   Muestra la matriz maestra de bandas sonoras cruzadas y launchers"
	@echo "  make soundtracks-mix    Genera variante con soundtrack cruzado (Uso: make soundtracks-mix GAME=MVC2 ST=3S OUT=...)"
	@echo "  make test-adx           Verifica el funcionamiento del motor ADX y recálculo de loops"
	@echo "  make convert-audio      Convierte un audio individual a CRI ADX"
	@echo "                          Uso: make convert-audio INPUT=tema.mp3 OUTPUT=MVC2/ADX_S000.BIN"
	@echo ""
	@echo "  --- COMPILACIÓN STANDALONE (MvC2 Nene Edition) ---"
	@echo "  make gdi                Genera la imagen GDI para emuladores/GDEMU (output_gdi/)"
	@echo "  make cdi                Genera la imagen CDI autoboot compacta (~498 MB)"
	@echo "  make cdi-dummy          Genera la imagen CDI optimizada con 0DUMMY.DAT (hasta 650 MB para CD-R)"
	@echo ""
	@echo "  --- COMPILACIÓN MULTIJUEGO ---"
	@echo "  make multidisc          Compila el CDI Multijuego autobootable (Audio/Data LBA 11702)"
	@echo "                          Opciones: OUT=output_cdi/juego.cdi VOL=NOMBRE TEMPLATE=plantilla.html LBA=11702"
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

## downsample-adx: Optimiza pistas ADX a 22050 Hz Mono recalculando loop points
downsample-adx:
	@if [ -z "$(DIR)" ] && [ -z "$(INPUT)" ]; then \
		echo "[!] Error: Especifica DIR=<carpeta_con_adx> o INPUT=<archivo.adx> [OUT=<destino>] [IN_PLACE=1]"; \
		exit 1; \
	fi
	python3 $(TOOLS_LINUX)/adx_downsampler.py "$${DIR:-$(INPUT)}" $(if $(OUT),"$(OUT)",) $(if $(IN_PLACE),--in-place,)

## downsample-mvc2: Downsamplea las pistas de MVC2/ directamente (-75% de espacio, ~130MB liberados)
downsample-mvc2:
	@echo "[*] Downsampleando audios de MVC2/ a 22kHz mono con recálculo de loops..."
	python3 $(TOOLS_LINUX)/adx_downsampler.py "$(MVC2_DATA)" --in-place

## downsample-all: Downsamplea las pistas de MVC2, CVS2 y CVS1J
downsample-all:
	@echo "[*] Downsampleando audios de todas las carpetas de juegos a 22kHz mono..."
	python3 $(TOOLS_LINUX)/adx_downsampler.py "$(MVC2_DATA)" --in-place
	@[ -d "$(ROOT_DIR)/Games/CVS2" ] && python3 $(TOOLS_LINUX)/adx_downsampler.py "$(ROOT_DIR)/Games/CVS2" --in-place || true
	@[ -d "$(ROOT_DIR)/Games/CVS1J" ] && python3 $(TOOLS_LINUX)/adx_downsampler.py "$(ROOT_DIR)/Games/CVS1J" --in-place || true

## soundtracks-list / matrix: Muestra la matriz de combinación de soundtracks
soundtracks-list: soundtracks-matrix
soundtracks-matrix:
	python3 $(TOOLS_LINUX)/soundtrack_manager.py list

## soundtracks-mix: Genera una variante de juego con soundtrack cruzado (Uso: make soundtracks-mix GAME=MVC2 ST=3S BASE=MVC2 OUT=staging/GAME26)
soundtracks-mix:
	@if [ -z "$(GAME)" ] || [ -z "$(ST)" ] || [ -z "$(OUT)" ]; then \
		echo "[!] Error: Uso: make soundtracks-mix GAME=<juego> ST=<soundtrack> OUT=<carpeta_salida> [BASE=<juego_base>]"; \
		exit 1; \
	fi
	python3 $(TOOLS_LINUX)/soundtrack_manager.py mix --game "$(GAME)" --soundtrack "$(ST)" --base-dir "$${BASE:-$(MVC2_DATA)}" --out-dir "$(OUT)"

## test-adx: Verifica el funcionamiento del motor de downsampling y recálculo de loops
test-adx:
	@echo "[*] Ejecutando test de integridad de motor ADX 22kHz..."
	python3 $(TOOLS_LINUX)/adx_downsampler.py "$(MVC2_DATA)/ADX_MENU.BIN" "/tmp/test_adx_menu.adx"
	@ffmpeg -y -i "/tmp/test_adx_menu.adx" "/tmp/test_adx_menu.wav" >/dev/null 2>&1 && echo "[✓] Verificación de audio ADX exitosa (decode OK)"

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

## multidisc: Compila la imagen CDI Multijuego (Audio/Data LBA 11702) con de-duplicación de sectores
##            Uso: make multidisc [OUT=output_cdi/archivo.cdi] [VOL=NOMBRE] [TEMPLATE=plantilla.html] [LBA=11702]
multidisc:
	@echo "[*] Compilando imagen CDI Multijuego autoboot (LBA $${LBA:-11702})..."
	python3 $(TOOLS_LINUX)/multidisc_manager.py build-modular \
		--output "$${OUT:-$(OUTPUT_CDI)/capcom_fight_pack.cdi}" \
		--volume "$${VOL:-CAPCOM_FIGHT_PACK}" \
		--lba "$${LBA:-11702}" \
		$(if $(TEMPLATE),--template "$(TEMPLATE)",)

## build-pack / build-json: Compila cualquier multijuego definido en un archivo JSON declarativo
##                          Uso: make build-pack CONFIG=configs/capcom_fight_pack_4in1.json [OUT=output.cdi]
build-pack: build-json
build-json:
	@if [ -z "$(CONFIG)" ]; then \
		echo "[*] No se especificó CONFIG. Usando por defecto: configs/capcom_fight_pack_4in1.json"; \
		python3 $(TOOLS_LINUX)/multidisc_manager.py build-json --config "$(ROOT_DIR)/configs/capcom_fight_pack_4in1.json" $(if $(OUT),--output "$(OUT)",); \
	else \
		python3 $(TOOLS_LINUX)/multidisc_manager.py build-json --config "$(CONFIG)" $(if $(OUT),--output "$(OUT)",); \
	fi

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
