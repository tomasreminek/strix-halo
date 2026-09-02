# Strix Halo recipes (measured)

Replicable configs from a **Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`)** box.

Every number below was measured on this machine. Forum screenshots, 3090 CUDA,
DGX Spark EXL3, and “128 GB recipe” claims are **not** copied as results.

Living dashboard (same numbers, plus video clips):
[strix-halo.html](http://hilbertkb.31.97.126.27.sslip.io/strix-halo.html)

## Hardware

| | |
|---|---|
| CPU / iGPU | AMD Ryzen AI MAX+ 395 · Radeon 8060S · `gfx1151` |
| Memory | 128 GB class unified. **This box reports 124 GiB** (`free -h`). That 4 GiB gap matters for 110+ GiB MoE. |
| OS | Pop!_OS / Linux 7.0.11, x86_64 |
| Rule | **One GPU-heavy job at a time.** Unload the LLM before ComfyUI, and vice versa. |

## Winners (2026-08)

| Workload | Winner | Decode / wall | Recipe |
|---|---|---|---|
| **Chat / lite worker** | Qwen3.8-Flash-Next AP-IQ4_XS + Nathanw **v0.7.3** Vulkan | **30.1 t/s** tg64 · pp16k **373 t/s** (+15% vs 0.7.2) | [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md) |
| **GLM-5.3-Flash (320B MoE)** | aj9o9 AJ-IQ2_XXS + Unsloth MIX **ROCm gfx1151** | **14.63 t/s** decode · **128k KV / 64k Hermes window** | [docs/glm-53-flash.md](docs/glm-53-flash.md) |
| **Full agent 27B** | Qwen3.8-27B ROCmFP4 FAST + MTP `n-max=2` | Czech **20.2 t/s** (73% acc) · no-draft **14.2 t/s** | [docs/qwen38-27b.md](docs/qwen38-27b.md) |
| **MiniMax H3 Czech video** | FP8 + Qwen3-VL 32B + Euler/simple 8–11 | 3s T2V **~11 min** · human 8/10 | [docs/minimax-h3.md](docs/minimax-h3.md) |

## Measured (2026-09-01) — Orca + MTP sidecar

Nathanw v0.7.3 + Orca Q4_K_M 3-shard + EasiiX sidecar: EN code **58.5 t/s** (95% acc), Czech **30.5 t/s** (70% acc). Not Telegram default. Details: [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md#measured-2026-09-01--orca-uncensored-q4_k_m--mtp-sidecar--nathanw-v073).

## Measured (2026-09-02) — Unsloth MIX b10715 is slower on this pair

Same Orca weights on Unsloth MIX `b10715-mix` **ROCm gfx1151** + `shared-Q8_0` MTP: Czech **25.6 t/s**, EN code **42.4 t/s**. EasiiX sidecar rejected on MIX. Vendor 1.67× is NVIDIA B200, not Hilbert. Keep Nathanw. Details: [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md#measured-2026-09-02--unsloth-mix-b10715-rocm-gfx1151--orca--shared-mtp).

## Do not mix tables

- Flash-Next **30 t/s** is a **different model** from 27B (~14–20 t/s) and from GLM (~14.6 t/s).
- julianmb/haloq38flash **56 t/s** is Flash-Next **MTP @ 8k**, not GLM. At 128k they report 19–27 t/s — slower than 30 t/s here without MTP.
- GLM **Vulkan 8.57 t/s** is not the Hilbert ceiling. Same GGUF on **ROCm gfx1151** is **14.63 t/s**.

## Docs

1. [Hardware & measurement rules](docs/00-hardware.md)
2. [GLM-5.3-Flash](docs/glm-53-flash.md) — download, bytes, ROCm vs Vulkan, OOM path
3. [Qwen3.8-Flash-Next](docs/qwen38-flash-next.md)
4. [Qwen3.8 27B](docs/qwen38-27b.md)
5. [MiniMax H3](docs/minimax-h3.md)
6. [Reddit post draft](docs/reddit-post.md)

## Licence

Recipes are MIT. Model weights stay under their own Hugging Face licences.
