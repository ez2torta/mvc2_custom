# Pull Request #1: Support PowerVR Mipmaps (Type 2/4) & Fix Symmetric ARGB1555 Color Conversion

> **Branch to submit**: `feat/powervr-mipmaps-and-color-fix`

## 📋 Summary

This PR fixes texture loading artifacts for PowerVR CLX2 textures that use Mipmapping (`Type 2` Twiddled Mipmap and `Type 4` VQ Mipmap) and fixes 5-bit to 8-bit channel expansion in `ARGB1555` to prevent color drift and loss of dynamic range.

---

## 🔍 Detailed Changes

### 1. PowerVR Mipmap Offset Calculation (`Type 2` & `Type 4`)
- **Issue**: For textures with mipmaps, the PowerVR architecture packs the lower-resolution mipmap levels ($1\times1, 2\times2, 4\times4 \dots \frac{W}{2}\times\frac{H}{2}$) sequentially before the base texture. Reading starting at byte 0 resulted in pixel misalignment and visual corruption in files such as `DM05TEX.BIN`, `DM07TEX.BIN`, and `DM08TEX.BIN`.
- **Fix**:
  - Added `src/utils/textures/getMipmapOffset.ts` implementing the closed-form geometric offset formula:
    $$\text{Offset}_{16\text{-bit}} = \left\lfloor \frac{\text{Width} \times \text{Height} - 4}{3} \right\rfloor \times 2 + 24 \text{ bytes}$$
    $$\text{Offset}_{\text{VQ}} = \left\lfloor \frac{\text{Width} \times \text{Height} - 4}{12} \right\rfloor + 6 \text{ bytes}$$
  - Updated `src/utils/textures/getTextureDefDataLength.ts` and `src/workers/loadTextureFileWorker.ts` to skip preceding mipmaps when loading the base texture.
  - Added unit test suite in `src/utils/textures/getMipmapOffset.spec.ts`.

### 2. Symmetric 5-bit to 8-bit ARGB1555 Color Conversion
- **Issue**: `argb1555ToRgba8888.ts` was previously using a linear multiplier of 8 (`val5 * 8`), mapping the maximum 5-bit value (31) to 248 instead of 255. When quantized back, channel values suffered from rounding errors and color degradation.
- **Fix**:
  - Implemented standard hardware bitwise expansion:
    $$\text{channel}_{8\text{-bit}} = (\text{val}_5 \ll 3) \mid (\text{val}_5 \gg 2)$$
  - Added `src/utils/textures/dm08CabRoundtrip.spec.ts` unit test verifying 100% bit-exact reversible roundtrip.

---

## 📁 Files in this PR (7 Files)

| File | Status | Purpose |
| :--- | :---: | :--- |
| `src/utils/textures/getMipmapOffset.ts` | **New** | Computes byte offset of preceding mipmap levels for PowerVR Type 2 and Type 4 textures. |
| `src/utils/textures/getMipmapOffset.spec.ts` | **New** | Unit tests for Type 2 (16-bit) and Type 4 (VQ) mipmap offset calculations. |
| `src/utils/textures/dm08CabRoundtrip.spec.ts` | **New** | Unit test validating bit-exact ARGB1555 roundtrip. |
| `src/utils/textures/VqFormatConstants.ts` | Modified | Exported `TWIDDLED_MIPMAP_TEXTURE_ENCODE_TYPE` (2) and `VQ_MIPMAP_TEXTURE_ENCODE_TYPE` (4). |
| `src/utils/textures/getTextureDefDataLength.ts` | Modified | Calculates full buffer length on disk including mipmaps. |
| `src/workers/loadTextureFileWorker.ts` | Modified | Applies mipmap offset when resolving `sourceLocation` for Type 2 textures. |
| `src/utils/color-conversions/argb1555ToRgba8888.ts` | Modified | Bitwise symmetric 5-bit to 8-bit color expansion. |

---

## ✅ Test Results

- All 28 Jest test suites passed (`npm test`):
  ```
  Test Suites: 28 passed, 28 total
  Tests:       141 passed, 141 total
  ```
