# Hardware and how we measure

Host: **AMD Ryzen AI MAX+ 395**, iGPU **Radeon 8060S**, ISA **`gfx1151`**.

`free -h` Mem total on this box is **124 GiB**, not 128. Community “128 GB Strix Halo”
recipes that leave ~5 GiB after a 112 GiB GGUF will OOM here (extra ~1.28 GiB radv
buffer). Treat **124 GiB** as the planning number unless you measured 128.

## Policy

- One GPU-heavy process. Flash-Next (~84–103 GiB) **XOR** 27B **XOR** ComfyUI (~50+ GiB).
- Prefill and decode are **separate** numbers. A single “N tok/s” headline is usually a lie.
- `llama-bench` without a working ICD **silently benches CPU** and still prints plausible t/s.
  Assert the backend column is `Vulkan` or `ROCm`.
- Qualitative gate = `llama-server` + `curl /v1/chat/completions`. **Never `llama-cli`**
  on huge-n_ctx GGUFs (Flash-Next default n_ctx is 262k).
- Compare Hugging Face **tree API `size`** to `stat -c%s`, not `ls -lh`.
- Logs on ext4 (`/tmp`). Do not truncate multi-tens-of-GB files on NTFS.

## ICD / library path (two opposite rules)

| Runtime | `VK_ICD_FILENAMES` | `LD_LIBRARY_PATH` |
|---|---|---|
| Nathanw portable Vulkan (Flash-Next, 27B Vulkan benches) | **set** to the bundle `radeon_icd.x86_64.json` | bundle `bin` + `driver` |
| Unsloth MIX Vulkan **or** ROCm gfx1151 (GLM) | **unset** (system ICD → `Available devices: (none)`) | the Unsloth extract dir only |

## Date

All winner rows: **2026-08-30** (Qwen) and **2026-08-31** (GLM). H3 Czech production
branch through **2026-08-29**.
