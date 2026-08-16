# 🚀 Compilador Declarativo Multijuego Dreamcast (JSON Engine)

El motor de compilación multidisco ahora permite definir **cualquier compilación multijuego mediante un archivo `.json` simple y legible**, sin necesidad de tocar código Python ni editar Makefiles complejos.

---

## 📄 1. Estructura de un Archivo de Configuración JSON

Ejemplo: [`configs/capcom_fight_pack_4in1.json`](file:///home/tortita/Coding/Github/Side/mvc2_custom/configs/capcom_fight_pack_4in1.json)

```json
{
  "volume_name": "CAPCOM_FIGHT_PACK",
  "base_lba": 11702,
  "output_cdi": "output_cdi/capcom_fight_pack.cdi",
  "menu_template": "Games/Frontend/DPWWW/templates/fightpack_4in1.html",
  "description": "Capcom Fighting Collection 4-en-1 para Sega Dreamcast",
  "games": [
    {
      "id": "GAME20",
      "name": "Marvel vs. Capcom 2 (Nene Edition)",
      "source_dir": "MVC2",
      "audio_pool": "Games/Frontend/ADXFILES/MVC_CUSTOM",
      "soundtrack_target_key": "MVC2",
      "generate_soundtracks": ["ALL", "SILENT"]
    },
    {
      "id": "JAPCVS",
      "name": "Capcom vs. SNK 2 (English v1.2)",
      "source_dir": "Games/CVS2",
      "audio_pool": "Games/Frontend/ADXFILES/CVS",
      "soundtrack_target_key": "CVS2",
      "generate_soundtracks": ["ALL", "SILENT"]
    },
    {
      "id": "CVS1J",
      "name": "Capcom vs. SNK (Millennium Fight 2000)",
      "source_dir": "Games/CVS1J",
      "audio_pool": "Games/Frontend/ADXFILES/CVS1",
      "soundtrack_target_key": "CVS1",
      "generate_soundtracks": ["ALL", "SILENT"]
    },
    {
      "id": "ST",
      "name": "Super Street Fighter II X: Grand Master Challenge",
      "source_dir": "Games/SSF2X",
      "soundtrack_target_key": "ST",
      "generate_soundtracks": ["ALL", "SILENT"]
    }
  ]
}
```

---

## 🛠️ 2. Opciones por cada Juego en la Lista

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `id` | `string` | Nombre del directorio destino en el disco (ej: `GAME20`, `JAPCVS`, `CVS1J`, `ST`). Mapea con `x-avefront://---.dream/proc/launch/<ID>`. |
| `name` | `string` | Nombre legible del juego para logs y diagnóstico. |
| `source_dir` | `string` | Carpeta de origen de los assets del juego (ej: `MVC2`, `Games/CVS2`, `Games/SSF2X`). |
| `audio_pool` | `string` | *(Opcional)* Carpeta con audios ADX optimizados/downsampleados para inyectar al juego. |
| `soundtrack_target_key` | `string` | Identificador del juego para el sistema de bandas sonoras (`MVC2`, `CVS2`, `CVS1`, `ST`, `3S`, `PF`). |
| `generate_soundtracks` | `array` | Lista de variantes a generar (`["ALL"]`, `["CVS2", "ST", "SILENT"]`, etc.). Utiliza *Shared Extents* (0 MB extra). |
| `custom_1st_read` | `string` | *(Opcional)* Reemplaza el ejecutable primario `1ST_READ.BIN` con un binario específico. |

---

## ⚡ 3. Cómo Compilar desde la Terminal

Puedes usar `make` o el CLI de Python directamente:

```bash
# Método 1: Vía Make
make build-pack CONFIG=configs/capcom_fight_pack_4in1.json

# Método 2: Vía CLI de Python
python3 Tools/linux/multidisc_manager.py build-json --config configs/capcom_fight_pack_4in1.json

# Sobrescribir la ruta de salida del CDI
make build-pack CONFIG=configs/template_custom_pack.json OUT=output_cdi/mi_disco_nuevo.cdi
```

---

## 📁 4. Plantillas Listas para Usar

* **[`configs/capcom_fight_pack_4in1.json`](file:///home/tortita/Coding/Github/Side/mvc2_custom/configs/capcom_fight_pack_4in1.json)**: Pack completo 4-en-1 (MvC2 + CvS2 + CvS1 + SSF2X).
* **[`configs/template_custom_pack.json`](file:///home/tortita/Coding/Github/Side/mvc2_custom/configs/template_custom_pack.json)**: Plantilla limpia para armar tu propia compilación con los juegos que tú elijas.
