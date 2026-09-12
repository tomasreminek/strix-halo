# Model comparison table · Strix Halo (measured)

Every number here was measured on **Hilbert** (Ryzen AI MAX+ 395 / Radeon 8060S gfx1151, 124 GiB, one GPU job).
Backend and method always stated: `llama-bench` (Vulkan unless noted) or `llama-server print_timing`. Do not mix tables.

## Master leaderboard

| Model (quant) | Backend / runtime | pp512 | pp16k | tg64 / decode | Server decode (prose) | Verdict |
|---|---|---:|---:|---|---|---|
| **Qwen3.8-Flash-Next AP-IQ4_XS** | Nathanw v0.7.3 Vulkan | 428 | 373 | **30.1** t/s | 29.4–30.5 EN/CZ | **Chat / lite winner** |
| **Qwen3.8-27B ROCmFP4 FAST** (+MTP n-max 2) | Laurent Vulkan HIP | 61 | 56 | 14.1 | **20.2** CZ (73% acc) | **Full agent winner** (cache-reuse) |
| **Qwen3.8-27B heretic-ara + MTP** | HIP ROCmFPX | 335* | 308* | 14.4 → **18.9** MTP | — | Uncensored worker |
| **Qwen3.8-27B cyjin IQ4_XS** | Nathanw | 334 | 308 | 13.3 | 13.3 | Dropped (slower than heretic) |
| **GLM-5.3-Flash AJ-IQ2_XXS (320B MoE)** | Unsloth MIX ROCm gfx1151 | ~100† | — | **14.63** | 14.4 @128k KV | Big-MoE winner (128k KV on this box) |
| **Signal 3.8-27B AP-Q4_K_XL** | Nathanw v0.7.3 Vulkan0 | **190.9** | **183.1** | **11.9** t/s | 19.3 CZ / 29.2 code (probe) | 2026-09-12 measured · MTP acc 0.60–0.90 |
| **Ornith 1.5-9B Q4_0 ROCMFP4** | Vulkan0 (local build) | **990.7** | **842.8** | **40.7** t/s | 34.2–38.9 (probe) | 2026-09-12 measured · fastest 27B-worker prefill |
| **Nex N2.5-mini ROCmFP4 STRIX_LEAN** | HaloFPX Vulkan0 | 650 | 581 | **81.6** t/s | 78.5 @8k | **Quality REJECT** (CZ/EN garbage; weights deleted) |
| **CIRU-STRIX-Orca (Qwen3.8 Flash)** | CIRU runtime MTP sidecar | _in progress (rebench)_ | — | — | — | Pending 2026-09-12 rebench |

\* cyjin/heretic numbers measured on qwen38-27b.md three-arm control rows.
\† GLM short-prompt prefill ~99–103 t/s (server, Unsloth MIX b10715).

## Detail 2026-09-12 kanban sweep (full numbers)

| Model | llama-bench pp512 (runs) | llama-bench pp16k (runs) | llama-bench tg64 (runs) | API probe prefill/decode (cold, warm, CZ, code, refusal) |
|---|---|---|---|---|
| Signal 3.8-27B AP-Q4_K_XL | 190.9 / 172.4 | 183.1 / 164.8 | 11.88 / 11.18 | 207.6→92.2 / 18.6–29.2 · refused=false |
| Ornith 1.5-9B Q4_0 ROCMFP4 | 990.7 / 694.8 | 842.8 / 560.2 | 40.72 / 36.51 | 750.8→287.6 / 34.2–38.9 · refused=false |
| CIRU-STRIX-Orca | — invalid JSON (bench) — | — | — | partial: 5.8 / 9.5 t/s (1 task) |

Evidence: `records/benchmarks/kanban-2026-09-12/` (bench JSON + probe JSON + server logs).
