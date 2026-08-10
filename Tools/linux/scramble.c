/*
 * scramble.c - SEGA Dreamcast binary scrambler / unscrambler
 * Based on Marcus Comstedt's scramble algorithm
 * 
 * Usage:
 *   scramble <input_file> <output_file>
 */

#include <stdio.h>
#include <stdlib.h>

static int scramble(const unsigned char *src, unsigned char *dst, int size) {
    int i, p;
    for (i = 0; i < size; i++) {
        p = ((i & 0x55555555) << 1) | ((i & 0xAAAAAAAA) >> 1);
        if (p < size) {
            dst[p] = src[i];
        }
    }
    return 0;
}

int main(int argc, char *argv[]) {
    FILE *fin, *fout;
    unsigned char *in_buf, *out_buf;
    long size;

    if (argc != 3) {
        fprintf(stderr, "Uso: %s <archivo_entrada> <archivo_salida>\n", argv[0]);
        fprintf(stderr, "Nota: Esta función es simétrica (sirve tanto para scramble como para descramble).\n");
        return 1;
    }

    fin = fopen(argv[1], "rb");
    if (!fin) {
        perror("Error al abrir archivo de entrada");
        return 1;
    }

    fseek(fin, 0, SEEK_END);
    size = ftell(fin);
    fseek(fin, 0, SEEK_SET);

    in_buf = (unsigned char *)malloc(size);
    out_buf = (unsigned char *)malloc(size);

    if (!in_buf || !out_buf) {
        fprintf(stderr, "Error de asignación de memoria (%ld bytes)\n", size);
        fclose(fin);
        return 1;
    }

    if (fread(in_buf, 1, size, fin) != (size_t)size) {
        perror("Error al leer archivo de entrada");
        free(in_buf);
        free(out_buf);
        fclose(fin);
        return 1;
    }
    fclose(fin);

    scramble(in_buf, out_buf, (int)size);

    fout = fopen(argv[2], "wb");
    if (!fout) {
        perror("Error al abrir archivo de salida");
        free(in_buf);
        free(out_buf);
        return 1;
    }

    if (fwrite(out_buf, 1, size, fout) != (size_t)size) {
        perror("Error al escribir archivo de salida");
        free(in_buf);
        free(out_buf);
        fclose(fout);
        return 1;
    }

    fclose(fout);
    free(in_buf);
    free(out_buf);

    printf("Procesado exitosamente: %s -> %s (%ld bytes)\n", argv[1], argv[2], size);
    return 0;
}
