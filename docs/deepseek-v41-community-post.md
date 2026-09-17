# DeepSeek V4.1 on a single Strix Halo

https://github.com/tomasreminek/strix-halo

I ran DeepSeek V4.1 Flash Q2 **overnight on one AMD Ryzen AI MAX+ 395 / Radeon 8060S (gfx1151) with 124 GiB unified memory** — the exact class of machine people call "128 GB Strix Halo". Full reproducible commands, exact checksums and the complete experiment matrix are in my repo: **https://github.com/tomasreminek/strix-halo** (start with `docs/deepseek-v41-single-strix-halo.md`).

## What DeepSeek V4.1 Flash Q2 did here

- It **runs** on a single Strix Halo via the kyuz0 `ds4` ROCm runtime with SSD expert streaming (measured tested host fix `869a09d`, ROCm 7.2.4, 8k context). Clean CLI recipe in the repo, `recipes/deepseek-v41/host-sqrt.patch`, pinned antirez Q2 GGUF with SHA-256.
- Three fresh-server repeated runs: **Python ~29.2 s, bugfix ~26.4 s, Czech chat ~20.4 s, JSON ~11.5 s, extraction ~8.4 s** full-request wall. Sandbox code passed; strict "code-only" formatting sometimes did not. Highest measured completion-token/full-request rate was **7.12 tok/s — that includes reasoning, it is not native decode**, and that request wall was 42.7 s.
- Real 64k prompts pass; **128k never produced a final answer** in a 905 s bounded calibration (inconclusive, not zero).
- Second overnight acceleration pass: **no replicated win**. Bigger expert caches hit active memory-pressure aborts; mapped-host expert slabs passed synthetic GPU checks but never completed faster real inference; MTP/DSpark unsupported on this exact V4.1 path.
- I had the exact local DeepSeek write a complete Three.js arcade game (Tapper-like, one HTML file): three attempts, **15,316 output tokens, ~62 minutes of model wall time, 3.9–4.2 end-to-end (non-decode) tok/s**. It produced a complete game, but the tested repair was **unplayable on a real phone**, and the needed mobile fixes were still being generated when I **stopped the experiment**.
- I stopped the overnight run. Weights, raw logs and every failed attempt are preserved.

## The actual winner: Qwen3.8 Flash-Next on native Halogen

Measured MTP decode with a quality overlay, prompts actually filled, 256 generated tokens: **44.66 tok/s short serving, 41.37 @~32k, 40.08 @~64k, 38.03 @~126k**. Czech, tool calls, strict JSON, Responses API and vision passed. One published caveat: the byte-identity gate between serial and MTP output stays under review. Recipe + caveats: `docs/qwen38-halogen.md`. Uncensored Orca fallback reaches 35.26 tok/s varied / 25.89 sustained @126k on Nathanw Vulkan (`docs/qwen38-flash-next.md`).

## GLM-5.3-Flash (320B MoE) also measured

**14.63 tok/s server decode** with `AJ-IQ2_XXS` (81.35 GiB) on Unsloth MIX ROCm gfx1151 — same GGUF on Vulkan is only **8.57 tok/s**, so the ROCm build is the lift, not a quant change. Runs with 128k KV / 64k agent window. Recipe: `docs/glm-53-flash.md`.

## One rule if you try this

Don't mix tables. DeepSeek request-wall numbers are not native decode; a 128k slot configured is not a 128k prompt filled; NVIDIA/3090 numbers don't transfer to gfx1151. My full measured comparison table, including rejects, lives in `docs/model-comparison.md`.

If you want to reproduce the DeepSeek baseline (including the exact `--ssd-streaming-cache-experts 24GB` fallback people can actually afford on this class of machine), the pinned download/verify/build/run commands are all here, with honest outcomes at each step:

https://github.com/tomasreminek/strix-halo
