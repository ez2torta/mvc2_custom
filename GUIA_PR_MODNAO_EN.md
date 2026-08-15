# Pull Request: Add PowerVR Mipmap Support, Symmetric ARGB1555 Color Correction, DM08CAB/DM08CHR Arcade Intro Decoders & Headless CLI

> **Note**: This Markdown file is ready to be used as the description/body of a GitHub Pull Request to the upstream [ModNao repository](https://github.com/).

---

## 📋 Summary

This PR addresses several key texture decoding and color fidelity issues in Marvel vs. Capcom 2 (and other Sega NAOMI / Dreamcast games using the PowerVR CLX2 graphics pipeline), introduces support for arcade intro promotional character files (`DM08CAB.BIN` and `DM08CHR.BIN`), and adds a headless CLI driver for batch texture dump and injection without browser DOM dependencies.

---

## 🔍 Key Improvements & Bug Fixes

### 1. PowerVR Mipmap Offset Handling (`Type 2` & `Type 4`)
- **Problem**: When textures use Mipmapping (`Type 2` Twiddled Mipmap or `Type 4` VQ Mipmap), the PowerVR hardware stores reduced sub-levels ($1\times1, 2\times2, 4\times4 \dots \frac{W}{2}\times\frac{H}{2}$) before the base texture. ModNao previously read from byte offset 0, causing mipmapped demo/stage textures (e.g. `DM05TEX`, `DM07TEX`, `DM08TEX`) to load with corrupted/shifted pixel data.
- **Solution**: 
  - Created `src/utils/textures/getMipmapOffset.ts` implementing the exact geometric formula:
    $$\text{Mipmap Offset (16-bit)} = \left\lfloor \frac{\text{Width} \times \text{Height} - 4}{3} \right\rfloor \times 2 + 24 \text{ bytes}$$
  - Updated `getTextureDefDataLength.ts` and `loadTextureFileWorker.ts` to skip previous mipmap levels when reading base textures.
  - Added unit tests in `src/utils/textures/getMipmapOffset.spec.ts`.

### 2. Symmetric 5-bit to 8-bit ARGB1555 Color Conversion
- **Problem**: In `argb1555ToRgba8888.ts`, 5-bit channels were expanded using a simple multiplication by 8 (`val5 * 8`), resulting in a maximum value of $31 \times 8 = 248$ instead of 255. When quantized back with `rgbaToArgb1555.ts`, rounding errors caused channel drift and green/red color distortion.
- **Solution**:
  - Implemented standard hardware bitwise expansion:
    $$\text{channel}_{8\text{-bit}} = (\text{val}_5 \ll 3) \mid (\text{val}_5 \gg 2)$$
  - This ensures 0 maps to 0, 31 maps to 255 symmetrically, and guarantees **100% bit-exact lossless roundtrip** between 16-bit ARGB1555 and 32-bit RGBA PNGs.

### 3. Support for Arcade Intro Files (`DM08CAB.BIN` & `DM08CHR.BIN`)
- **`DM08CAB.BIN` (Cable & Ruby Heart Intro Art)**:
  - Discovered that `DM08CAB.BIN` contains **two 512x512 ARGB1555 full-resolution illustrations** with 1-bit alpha transparency: **Cable** (offset `0x0`) and **Ruby Heart** (offset `0x80000`).
  - Added dedicated extraction and injection logic yielding a **0-byte difference bit-exact roundtrip** (`cmp -l` verified).
  - Added test suite in `src/utils/textures/dm08CabRoundtrip.spec.ts`.
- **`DM08CHR.BIN` (56 Character Intro Sprites)**:
  - Added decompression and pointer-table repackaging for all 56 character intro portraits using LZSS + Morton-Z twiddling.

### 4. Headless CLI Engine (`src/cli/`)
- Added `src/cli/mvc2TextureManager.ts` and `src/cli/index.ts` allowing users to dump and inject all supported MvC2 textures via Node.js scripts (`npm run textures:dump` and `npm run textures:inject`) using `jimp` instead of headless browser canvas.

---

## 📁 Files Changed

| File | Status | Description |
| :--- | :---: | :--- |
| `src/utils/textures/getMipmapOffset.ts` | **New** | Computes byte offset of preceding mipmap levels for PowerVR Type 2 and Type 4 textures. |
| `src/utils/textures/getMipmapOffset.spec.ts` | **New** | Unit tests for Type 2 (16-bit) and Type 4 (VQ) mipmap offset calculations. |
| `src/utils/textures/dm08CabRoundtrip.spec.ts` | **New** | Unit test validating 100% bit-exact roundtrip for Cable & Ruby Heart ARGB1555 textures. |
| `src/utils/textures/VqFormatConstants.ts` | Modified | Exported `TWIDDLED_MIPMAP_TEXTURE_ENCODE_TYPE` (2) and `VQ_MIPMAP_TEXTURE_ENCODE_TYPE` (4). |
| `src/utils/textures/getTextureDefDataLength.ts` | Modified | Integrated mipmap length calculations into texture buffer size resolution. |
| `src/workers/loadTextureFileWorker.ts` | Modified | Applied mipmap offset when resolving `sourceLocation` for Type 2 textures. |
| `src/utils/color-conversions/argb1555ToRgba8888.ts` | Modified | Replaced `* 8` with bitwise symmetric expansion `(v << 3) | (v >> 2)`. |
| `src/cli/mvc2TextureManager.ts` | **New** | Core headless texture extraction & injection engine. |
| `src/cli/index.ts` | **New** | Command-line interface entry point (`dump`, `inject`, `dump-file`, `inject-file`). |
| `package.json` | Modified | Added `jimp` dependency and `textures:dump` / `textures:inject` npm scripts. |

---

## ✅ Test & Verification Results

- **Unit Tests**: All **28 test suites** and **141 tests passed** (`npm test`):
  ```
  Test Suites: 28 passed, 28 total
  Tests:       141 passed, 141 total
  Snapshots:   2 passed, 2 total
  ```
- **Roundtrip Validation**:
  - Full game extraction: Successfully dumped **709 PNG textures** across 160 files.
  - Re-injection verification: Tested against original `.BIN` files with `cmp -l`, achieving 0 byte discrepancies on test files.
