# Strix Halo recipes (measured)

## Hardware

| | |
|---|---|
| CPU / iGPU | AMD Ryzen AI MAX+ 395 · Radeon 8060S · `gfx1151` |
| Memory | 128 GB class unified. **This box reports 124 GiB** (`free -h`). That 4 GiB gap matters for 110+ GiB MoE. |
| OS | Pop!_OS / Linux 7.0.11, x86_64 |
| Rule | **One GPU-heavy job at a time.** Unload the LLM before ComfyUI, and vice versa. |

## 🏆 Overall winner: Qwen3.8 Flash-Next on native Halogen (quality overlay, MTP)

**44.66 tok/s short serving · 41.37 @~32k · 40.08 @~64k · 38.03 @~126k** (MTP decode, prompts actually filled, 256 generated tokens). Czech with diacritics, sandbox Python, OpenAI tool calls, strict JSON, Responses API and vision OCR all pass. The serial-vs-MTP byte-identity gate remains under review, published as a caveat, not hidden. Engine is closed source (`halogen-flash-server:0.11.0`). Full recipe, pinned hashes and download commands: **[docs/qwen38-halogen.md](docs/qwen38-halogen.md)**.

Everything else — including overnight DeepSeek V4.1 attempts and GLM-5.3-Flash — is below the winner.

## Master test table (2026-09-17)

| Workload | Winner | Decode / wall | Recipe |
|---|---|---|---|
| **Overall main model** | **Native Halogen Qwen3.8-Flash-Next** · quality overlay · 128k slot | **44.66 t/s** short · **40.08 t/s @64k** · **38.03 t/s @~126k** | [docs/qwen38-halogen.md](docs/qwen38-halogen.md) |
| **Uncensored fallback** | OrcaRouter Q4_K_M + EasiiX Q8_0 MTP · Nathanw **v0.7.6** Vulkan | **35.26 t/s** varied · **27.69 @64k** · **25.89 sustained @126k** | [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md) |
| **GLM-5.3-Flash (320B MoE)** | aj9o9 AJ-IQ2_XXS + Unsloth MIX **ROCm gfx1151** | **14.63 t/s** decode · **128k KV / 64k Hermes window** | [docs/glm-53-flash.md](docs/glm-53-flash.md) |
| **Full agent 27B** | Qwen3.8-27B ROCmFP4 FAST + MTP `n-max=2` | Czech **20.2 t/s** (73% acc) · no-draft **14.2 t/s** | [docs/qwen38-27b.md](docs/qwen38-27b.md) |
| **DeepSeek V4.1 Flash Q2 (340 GiB, SSD-streamed)** | Runs on single Strix Halo, **not a speed winner**; user stopped the experiment | **7.12 tok/s** completion incl. reasoning (**not native decode**) · coding/Czech medians 29.2/26.4/**20.4** s | [docs/deepseek-v41-single-strix-halo.md](docs/deepseek-v41-single-strix-halo.md) · [docs/deepseek-v41-night-20260917.md](docs/deepseek-v41-night-20260917.md) |
| **MiniMax H3 Czech video** | FP8 + Qwen3-VL 32B + Euler/simple 8–11 | 3s T2V **~11 min** · human 8/10 | [docs/minimax-h3.md](docs/minimax-h3.md) |

### DeepSeek V4.1 detail (user stopped the overnight run)

DeepSeek V4.1 Flash Q2 runs on this box via the kyuz0 `ds4` ROCm runtime with SSD expert streaming; measured host portability fix `869a09d`, ROCm 7.2.4, `--ssd-streaming-cache-experts`, `--ctx 8192`, `--batched-session 1`. Exact checkpoint 365,713,686,528 B / SHA-256 `1ce6a8f8806205c…` in the [full report](docs/deepseek-v41-single-strix-halo.md). Game-code trial: the model itself wrote a complete Three.js Tapper-inspired HTML over three attempts (15,316 output tokens, 3,704.68 s model wall). generate02/repair03 passed transport but real desktop/mobile QA rejected the core service/return loop; the owner found the final build unusable on a real phone and **stopped the experiment**. Exact per-attempt data in `records/benchmarks/deepseek-v41-tapper-20260917/measurements.json`. Complete reproducible commands, checksums and every failure: **[docs/deepseek-v41-single-strix-halo.md](docs/deepseek-v41-single-strix-halo.md)**.

### Qwen3.8 Flash-Next (uncensored Orca route) detail

Real-channel series (same repo → Nathanw v0.7.6 → today) measured: code **58.5 t/s** (95% acc) / Czech **30.5 t/s** (70% acc, 2026-09-01) on v0.7.3; Unsloth MIX b10715 slower (25.6 / 42.4) — vendor 1.67× claim is NVIDIA B200, keep Nathanw; matching Uncensored MTP-draft ≈ EasiiX (Czech +5%, 73% vs 66% acc); llama.cpp PR #28136 `on-direct` +10.7% cold prefill only; OrcaRouter Q4_K_M + EasiiX Q8_0 MTP on Nathanw **v0.7.6** Vulkan reaches **35.26 t/s** varied / **27.69 @64k** / **25.89 sustained @~126k**. Uncensored IQ4_XS on Halogen stays loader-blocked (dense `Q5_K` vs required `Q8_0`). All details and exact runlinks: **[docs/qwen38-flash-next.md](docs/qwen38-flash-next.md)**.

### GLM-5.3-Flash detail

Same AJ-IQ2_XXS GGUF, same flags: **ROCm 14.63 t/s vs Vulkan 8.57 t/s** (the ROCm build is the lift, not a quant change). Runs with 128k KV / 64k window. Architectural path is `glm5next` (open PR #27754), so Unsloth MIX build required. Vendor CUDA 3090 11.5 t/s does not transfer. All details: **[docs/glm-53-flash.md](docs/glm-53-flash.md)**.

Every number here was measured on this machine. Forum screenshots, 3090 CUDA,
DGX Spark EXL3, and “128 GB recipe” claims are **not** copied as results.

Living dashboard (same numbers, plus video clips):
[strix-halo.html](http://hilbertkb.31.97.126.27.sslip.io/strix-halo.html)

## DeepSeek V4.1 Flash Q2 · second pass 2026-09-17

No replicated useful acceleration certified. Cache24 is a working lower-residency fallback, not a speed winner; repeated cache80 pressure aborts qualify the earlier practical recommendation. Prefix reuse is a single exploratory observation, not a general decode gain. [Second-pass report](docs/deepseek-v41-speed2-20260917.md), [single-Strix-Halo deep dive + exact DeepSeek guides](docs/deepseek-v41-single-strix-halo.md), [comparison table](docs/model-comparison.md). The model-authored Tapper coding trial was stopped by the user after repair03 was rejected as unplayable on a physical phone; **no accepted mobile build exists yet** (details and exact timings in the deep dive).


## Historical measured series (full background)

Nathanw v0.7.3 + Orca Q4_K_M 3-shard + EasiiX sidecar era entries, PR #28136, MIX b10715, Nex N2.5 Mini reject and everything else stays below unchanged.

## Measured (2026-09-01) — Orca + MTP sidecar

Nathanw v0.7.3 + Orca Q4_K_M 3-shard + EasiiX sidecar: EN code **58.5 t/s** (95% acc), Czech **30.5 t/s** (70% acc). Not Telegram default. Details: [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md#measured-2026-09-01--orca-uncensored-q4_k_m--mtp-sidecar--nathanw-v073).

## Measured (2026-09-02) — Unsloth MIX b10715 is slower on this pair

Same Orca weights on Unsloth MIX `b10715-mix` **ROCm gfx1151** + `shared-Q8_0` MTP: Czech **25.6 t/s**, EN code **42.4 t/s**. EasiiX sidecar rejected on MIX. Vendor 1.67× is NVIDIA B200, not Hilbert. Keep Nathanw. Details: [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md#measured-2026-09-02--unsloth-mix-b10715-rocm-gfx1151--orca--shared-mtp).

## Measured (2026-09-03) — matching Uncensored MTP-draft vs EasiiX

Same-day `:18090` A/B, Nathanw v0.7.3, n-max 7. Hub `MTP-draft.gguf` does **not** load on Nathanw (`output_hc_norm.weight` missing) — Unsloth layout. After a local 3-tensor rename: Czech **32.3 vs 30.7 t/s** (+5%, acc 73% vs 66%), EN code wash (~50 t/s). MIX + Hub file: 27.0 / 44.9 — still slower. **Keep EasiiX in production.** Details: [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md#measured-2026-09-03--matching-uncensored-mtp-draft-vs-easiix).

## Measured (2026-09-03) — llama.cpp PR #28136 `on-direct` is +10.7% cold prefill, not 2–3×

HIP gfx1151 build of ggml-org + [PR #28136](https://github.com/ggml-org/llama.cpp/pull/28136) (`c6a9e5c`) vs mmap `--lazy-mode on`. Same AP-IQ4_XS. Port `:18090`. Cold **190.4 → 210.7 t/s (+10.7%)**. Warm wash. Decode not measured. Nathanw v0.7.3 has no `on-direct`. Not production. Do not mix into the 30 t/s decode table. Details: [docs/qwen38-flash-next.md](docs/qwen38-flash-next.md#measured-2026-09-03--llama-cpp-pr-28136-on-direct-pread-vs-mmap).

## Do not mix tables

- Flash-Next **30 t/s** is a **different model** from 27B (~14–20 t/s) and from GLM (~14.6 t/s).
- PR #28136 `on-direct` is a **cold-prefill SSD-read** delta on AP-IQ4 (+10.7% here), not a decode winner and not the DGX Spark 2–3× claim.
- julianmb/haloq38flash **56 t/s** is Flash-Next **MTP @ 8k**, not GLM. At 128k they report 19–27 t/s — slower than 30 t/s here without MTP.
- GLM **Vulkan 8.57 t/s** is not the Hilbert ceiling. Same GGUF on **ROCm gfx1151** is **14.63 t/s**.
- **Nex N2.5 Mini** (HaloFPX Vulkan, 2026-09-09): llama-bench tg64 **81.6 t/s** / pp512 **650**. Quality **reject** (Czech/EN garbage; thinking-on = 0 content). Not a winner. [docs/nex-n25-mini.md](docs/nex-n25-mini.md). Do not mix into Flash 30 t/s.

## Docs

1. [Hardware & measurement rules](docs/00-hardware.md)
2. [GLM-5.3-Flash](docs/glm-53-flash.md) — download, bytes, ROCm vs Vulkan, OOM path
3. [Qwen3.8 Flash-Next · native Halogen winner](docs/qwen38-halogen.md)
4. [Qwen3.8-Flash-Next · llama.cpp / Orca](docs/qwen38-flash-next.md)
5. [Qwen3.8 27B](docs/qwen38-27b.md)
6. [MiniMax H3](docs/minimax-h3.md)
7. [Nex N2.5 Mini (reject)](docs/nex-n25-mini.md)
8. [Model comparison · master table](docs/model-comparison.md)
9. [Kanban 2026-09-12 benchmark sweep](docs/kanban-2026-09-12.md)
10. [Reddit post draft](docs/reddit-post.md)

## Licence

Recipes are MIT. Model weights stay under their own Hugging Face licences.
