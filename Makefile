# ==============================================================================
# Makefile - Marvel vs Capcom 2 (Dreamcast) Modding & Build Pipeline
# ==============================================================================

SHELL := /bin/bash
ROOT_DIR := $(shell pwd)
TOOLS_LINUX := $(ROOT_DIR)/Tools/linux
MODNAO_DIR := $(ROOT_DIR)/Tools/modnao
MVC2_DATA := $(ROOT_DIR)/MVC2
TEXTURES_DIR := $(ROOT_DIR)/Extracted_Textures
OUTPUT_GDI := $(ROOT_DIR)/output_gdi
OUTPUT_CDI := $(ROOT_DIR)/output_cdi

.PHONY: all help build-tools extract-textures dump-textures inject-textures pack-textures gdi cdi convert-audio scramble unscramble clean

all: help

## help: Muestra este mensaje de ayuda
help:
	@echo "========================================================================"
	@echo "    Marvel vs Capcom 2 (Dreamcast) - Modding & Build Pipeline"
	@echo "========================================================================"
	@echo "Comandos disponibles:"
	@echo ""
	@echo "  --- TEXTURAS (ModNao Engine) ---"
	@echo "  make extract-textures   Extrae TODAS las texturas de MVC2 a PNG (Extracted_Textures/)"
	@echo "  make inject-textures    Reinyecta las texturas PNG modificadas a la carpeta MVC2/"
	@echo ""
	@echo "  --- COMPILACIÓN DE IMÁGENES ---"
	@echo "  make gdi                Genera la imagen GDI para emuladores/GDEMU (output_gdi/)"
	@echo "  make cdi                Genera la imagen CDI autoboot para CD-R (output_cdi/)"
	@echo ""
	@echo "  --- AUDIO Y HERRAMIENTAS ---"
	@echo "  make convert-audio      Convierte un audio a CRI ADX con FFmpeg"
	@echo "                          Uso: make convert-audio INPUT=tema.mp3 OUTPUT=MVC2/ADX_S000.BIN"
	@echo "  make scramble           Scramblea un binario SH-4 (Uso: make scramble INPUT=... OUTPUT=...)"
	@echo "  make unscramble         Descramblea un binario SH-4 (Uso: make unscramble INPUT=... OUTPUT=...)"
	@echo "  make build-tools        Compila herramientas nativas e instala dependencias de ModNao"
	@echo "  make clean              Limpia imágenes generadas y archivos temporales"
	@echo "========================================================================"

## build-tools: Compila binarios nativos (scramble) e instala dependencias de modnao
build-tools:
	@echo "[*] Compilando herramienta scramble en C..."
	gcc -O2 $(TOOLS_LINUX)/scramble.c -o $(TOOLS_LINUX)/scramble
	@echo "[*] Verificando dependencias de ModNao..."
	cd $(MODNAO_DIR) && npm install --silent
	@echo "[✓] Herramientas listas."

## extract-textures / dump-textures: Extrae todas las texturas de MVC2 a PNG
extract-textures: dump-textures
dump-textures:
	@echo "[*] Extrayendo todas las texturas con ModNao..."
	$(TOOLS_LINUX)/export_textures.sh "$(MVC2_DATA)" "$(TEXTURES_DIR)"

## inject-textures / pack-textures: Reinyecta las texturas editadas a los .BIN
inject-textures: pack-textures
pack-textures:
	@echo "[*] Reinyectando texturas modificadas a MVC2/..."
	$(TOOLS_LINUX)/import_textures.sh "$(TEXTURES_DIR)" "$(MVC2_DATA)" "$(MVC2_DATA)"

## gdi: Genera la imagen GDI completa (disc.gdi, track01, track02, track03)
gdi:
	@echo "[*] Generando imagen GDI..."
	python3 $(TOOLS_LINUX)/build_gdi.py "$(OUTPUT_GDI)"

## cdi: Genera la imagen CDI autobootable
cdi:
	@echo "[*] Generando imagen CDI..."
	$(TOOLS_LINUX)/build_cdi.sh "$(OUTPUT_CDI)"

## convert-audio: Convierte audio a ADX
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
