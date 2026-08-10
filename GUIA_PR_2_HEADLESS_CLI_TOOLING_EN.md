# Pull Request #2: Add Headless CLI Driver for Batch Texture Dump & Re-Injection

> **Branch to submit**: `feat/headless-cli-driver`

## 📋 Summary

This PR adds a standalone headless command-line interface (CLI) to ModNao, enabling batch texture extraction and injection for Marvel vs. Capcom 2 (and related games) directly via terminal scripts without requiring a browser window or browser DOM canvas environment.

---

## 🔍 Key Features

### 1. Pure Node.js Batch Operations
- Uses `jimp` for reading and writing 32-bit PNG images in headless Node.js environments.
- Re-uses ModNao's core serialization workers and algorithms (`exportTextureDefRegionWorker`, `exportTextureFileWorker`, `loadTextureFileWorker`, `compressLzssBuffer`, `decompressLzssBuffer`, `decompressVqBuffer`).

### 2. Comprehensive Game Support
- **Stages**: Automatically scans and processes `STGxxPOL.BIN` + `STGxxTEX.BIN`.
- **Demos & Effects**: Processes `DMxxPOL.BIN` + `DMxxTEX.BIN`, `EFKYPOL.BIN` + `EFKYTEX.BIN`.
- **Arcade Intro Illustrations**: Supports `DM08CAB.BIN` (512x512 Cable and Ruby Heart) and `DM08CHR.BIN` (56 character intro sprites).
- **Character Portraits**: Processes `PLxx_FAC.BIN` (Lifebars, Hyper & VS portraits with LZSS + VQ) and `PLxx_WIN.BIN` (Win portraits).
- **Menus & Interfaces**: Processes `SELSTG.BIN`, `SELTEX.BIN`, `SELVMJ.BIN`, `SELVMU.BIN`, `ENDDCTEX.BIN`, `ENDNMTEX.BIN`.

### 3. CLI Commands & NPM Scripts
- Added npm script entries in `package.json`:
  ```bash
  # Batch extraction of all supported game textures to PNG
  npm run textures:dump <mvc2_dir> <output_png_dir>

  # Batch re-injection of modified PNGs back into .BIN files
  npm run textures:inject <png_dir> <mvc2_template_dir> <output_bin_dir>
  ```
- Granular single-file utilities:
  ```bash
  npx tsx src/cli/index.ts dump-file <bin_file> <output_dir> [pol_file]
  npx tsx src/cli/index.ts inject-file <bin_orig> <png_dir> <bin_out> [pol_file]
  ```

---

## 📁 Files in this PR (3 Files)

| File | Status | Purpose |
| :--- | :---: | :--- |
| `src/cli/mvc2TextureManager.ts` | **New** | Core headless extraction and injection routines with roundtrip support. |
| `src/cli/index.ts` | **New** | CLI driver entry point with argument parsing and subcommands. |
| `package.json` | Modified | Added `jimp` dependency and `textures:dump` / `textures:inject` npm scripts. |

---

## ✅ Verification

- Verified complete game extraction (709 PNG textures dumped).
- Verified full roundtrip injection with binary verification across all supported formats.
