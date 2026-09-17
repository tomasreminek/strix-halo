# DeepSeek V4.1 on a single Strix Halo (AMD Strix Halo, 128 GB unified)

https://github.com/tomasreminek/strix-halo

I spent an overnight run testing **DeepSeek V4.1 Flash Q2 (the ~340 GiB MoE) on one AMD Ryzen AI MAX+ 395 / Radeon 8060S (gfx1151) with 124 GiB of unified memory** — a single Strix Halo box, no dGPU. Full reproducible commands, exact checksums, every failed attempt and the complete experiment matrix are public in my repo: **https://github.com/tomasreminek/strix-halo** (start with `docs/deepseek-v41-single-strix-halo.md`).

## Short version

It **runs** on a single Strix Halo — via the kyuz0 `ds4` ROCm runtime with SSD expert streaming (`--ssd-streaming-cache-experts`, ROCm 7.2.4, 8k context, one little host-side patch included in the repo). But it is **not a practical winner here**, and I stopped the experiment. Small coding/Czech tests worked at three-fresh-server medians of **29.2 s (Python)**, **26.4 s (bugfix)**, **20.4 s (Czech)**, full-request wall — and the highest completion-token rate was **7.12 tok/s including reasoning, which is not native decode**. Real 64k prompts pass; **128k never produced a final answer** in a 905 s bounded calibration. Every acceleration idea (larger caches, read-worker scaling, mapped host memory, MTP/DSpark) either pressure-aborted or was unsupported on this exact model path; nothing was replicated as a win.

## The coding-as-benchmark twist

I also had the exact local DeepSeek itself write a complete Three.js arcade game (Tapper-like, one HTML file, desktop + mobile controls). Four attempts: **20,575 output tokens, ~83 minutes of model wall time, ~3.9–4.2 end-to-end tok/s** (not decode). It produced complete HTML every time after the first, but every build failed my real desktop/mobile QA or my own phone test, so **I stopped it with an honest zero accepted games**. Failed attempts stay in the ledger — I think "can the model actually deliver a working artifact" is the benchmark that matters most.

## The actual winner: Qwen3.8 Flash-Next on native Halogen

Same box. Measured MTP decode with quality overlay, prompts actually filled, 256 generated tokens:

- **44.66 tok/s** short serving
- **41.37 @ ~32k**
- **40.08 @ ~64k**  
- **38.03 @ ~126k**

Czech with diacritics, sandbox Python, OpenAI tool calls, strict JSON, Responses API and vision OCR all pass. One published caveat: the byte-identity gate between serial and MTP output remains under review; engine is closed source. Recipe + caveats: `docs/qwen38-halogen.md`. Uncensored Orca fallback: **35.26 t/s varied / 25.89 sustained @126k** on Nathanw v0.7.6 Vulkan (`docs/qwen38-flash-next.md`).

## GLM-5.3-Flash (320B MoE) also measured

**14.63 tok/s server decode** with `AJ-IQ2_XXS` (81.35 GiB) on Unsloth MIX ROCm gfx1151 — same GGUF on Vulkan is only **8.57 tok/s**, so the ROCm build is the lift, not the quant change. Recipe: `docs/glm-53-flash.md`.

## One rule if you try any of this

Don't mix tables. DeepSeek request-wall numbers are not native decode. A 128k slot configured is not a 128k prompt filled. NVIDIA/3090 numbers don't transfer to gfx1151. My whole measured comparison table, including rejects, is in `docs/model-comparison.md`.

If you want to reproduce the DeepSeek baseline (including the exact `--ssd-streaming-cache-experts` fallback people can actually afford on this class of machine), the pinned model download / verify / build / run commands are all here, with honest outcomes at each step:

https://github.com/tomasreminek/strix-halo
