# Strix Halo recipes (measured)

## Hardware

| | |
|---|---|
| CPU / iGPU | AMD Ryzen AI MAX+ 395 · Radeon 8060S · `gfx1151` |
| Memory | 128 GB class unified. **This box reports 124 GiB** (`free -h`). That 4 GiB gap matters for 110+ GiB MoE. |
| OS | Pop!_OS / Linux 7.0.11, x86_64 |
| Rule | **One GPU-heavy job at a time.** Unload the LLM before ComfyUI, and vice versa. |

## All LLM tests · results and evidence

**Latest measured Strata candidate (2026-10-06): OrcaRouter Qwen3.8 Flash-Next Uncensored IQ3_XXS, Strata server v0.1.40.1 / stock v0.1.40 HIP engine, gfx1151 fast mode, prefill 16384, MTP4 with an 8192-token draft attention window.** Verified real 64k/128k context fixtures and bounded lifecycle; **not yet qualified as the long-term game-coding worker**. Fast mode changes numerics. Historical Halogen results use different weights/quantization and are not a current matched A/B. At the latest runtime readback, Strata and Halogen were stopped; no chat routing or permanent worker replacement was made. Dates below are test dates, not release dates.

| Date tested | Model / tested configuration | Measured result or gate | Outcome and full test |
|---|---|---|---|
| **2026-10-06** | **Strata server v0.1.40.1 · Orca Uncensored IQ3_XXS · HIP fast · prefill 16384 · MTP4/window8192** | At **30k**, three independent-process medians: **1301 tok/s prefill / 44.33 tok/s decode / 32.65 s request**. At **126k + 420 output**: **1272 / 42.44 tok/s / 109.23 s**; cached decode **43.43 tok/s**. Growing history: 126,450 input, 126,420 cached, 27 output in **1.12 s** | **39/39 context records, 17/17 short checks passed**; server suite 452 tests, 10 skips, no failures. Clean teardown; multi-file game coding and soak pending. [Report](docs/strata-v01401-20261006.md) · [JSON](docs/strata-v01401-20261006-summary.json) |
| **2026-10-06** | **Strata v0.1.40 · Orca Qwen3.8 Flash-Next Uncensored IQ3_XXS · HIP gfx1151 + MTP4** | New-prefix decode **43.6 / 41.8 / 41.5 / 38.7 tok/s** at actual **7.6k / 30k / 62k / 126k** prompts; cached **44.0 / 42.4 / 42.4 / 39.4**. New-prefix prefill **324.3 / 312.2 / 297.4 / 287.1 tok/s** | **Historical first run**: inference completed, followed by unclean reboot of unknown cause. Independent retest completed cleanly; NTFS access recovered after Windows chkdsk. Superseded for speed by the tuned row above. [Full report](docs/strata-v0140-strix-halo-20261006.md) · [machine-readable results](docs/strata-v0140-strix-halo-20261006-summary.json) |
| **2026-09-20–28** | **Halogen Qwen3.8 Flash-Next Abliterated** · HGN+patched experts+overlay, MTP | 28 Sep matched HTTP: cold/cached 21.71/11.45 s @9.6k; 66.85/12.27 s @62.4k; 126.11/12.83 s @127.6k. Cold decode 32.64/31.36/30.45 tok/s | **Historical preferred uncensored worker**; [abliterated A/B](docs/qwen38-halogen-abliterated.md) · [Gufo PR #91 end-to-end A/B](docs/gufo-pr91-halogen-e2e-20260928.md) · [historical native Gufo comparison](docs/flash-next-gufo-ciru-halogen-20260925.md) |
| 2026-09-28 | Gufo official base UD-Q4_K_XL · `strix-llama.cpp` PR #91 versus fork master | Cold @~127.5k: master 221.88 s → PR 181.53 s; Halogen 126.11 s. PR decode 21.15 tok/s, cached 19.90 s | **PR improves fork prefill but loses full requests to Halogen**; distinct from older native Gufo runtime. [Method/results](docs/gufo-pr91-halogen-e2e-20260928.md) · [18 raw responses](records/benchmarks/gufo-pr91-halogen-20260928/) |
| 2026-09-21, 25 | Ornith 1.5 9B Abliterated ROCmFP4 Strix Lean | Hermes tool loop, 63k and 117.8k retrieval pass; ~62k simultaneous Halogen control | **Local chat/task candidate**; [agent gates](docs/ornith-abliterated-20260921.md) · [coexistence correction](docs/ornith-halogen-coexistence-correction.md) |
| 2026-09-24–25 | Gufo + official Unsloth base UD-Q4_K_XL, serial, MTP off | 25.74 @9.5k; 22.94 / 22.88–22.89 @62.4k; 21.05 / 20.98–20.99 @127.5k tok/s | Cold ~127.5k wall **113.47 s** (Halogen 125.47 s); not uncensored; [report](docs/flash-next-gufo-ciru-halogen-20260925.md) · [raw records](records/benchmarks/flash-next-september-2026/README.md) |
| 2026-09-24–25 | CIRU Orca v4.4.1 + PLE + Q8 MTP4 | 30.94 / 36.31 @47-token short; 17.24 / 19.12 @62.4k tok/s. No MTP: 23.67 / 27.37 short | **Research option**; 128k not tested, deep coexistence memory pressure; [report](docs/flash-next-gufo-ciru-halogen-20260925.md) |
| 2026-09-16 | Native **aligned** Halogen quality overlay + MTP | 44.66 short; 40.08 @64k; 38.03 @~126k tok/s | Historical **aligned performance reference**, not current uncensored weights; [report](docs/qwen38-halogen.md) |
| 2026-09-01–17 | OrcaRouter uncensored Flash-Next Q4_K_M + EasiiX Q8 MTP, Nathanw Vulkan | v0.7.6: 35.26 varied; 27.69 @64k; 25.89 @126k tok/s. Earlier v0.7.3 Czech 30.5 / code 58.5 | Historical uncensored llama.cpp alternative; [runtime sweep](docs/qwen38-flash-next.md) |
| 2026-09-20 | **Signal 3.8 Flash Next** 177B MoE AP-Q4_K_XL | 21.9–22.0 tok/s on three 256-token runs with a 64k *configured slot*, without MTP; draft layout incompatible; Halogen external-GGUF trunk blocked | Valid llama.cpp no-draft decode, **no filled-64k or Halogen speed result**; [report](docs/signal-38-flash-next-2026-09-20.md) |
| 2026-09-12 | **Signal 3.8 27B** AP-Q4_K_XL | llama-bench pp512 190.9, pp16k 183.1, tg64 11.9 t/s; API Czech/code 19.3/29.2 | Separate 27B model, not Signal Flash Next; [Kanban sweep](docs/kanban-2026-09-12.md) |
| 2026-09-12 | CIRU-STRIX-Orca **v3**, PLE+MTP depth 6 | ~3.3 tok/s decode, MTP accept 0.25–0.32; pressure/timeout | **Rejected in v3**; do not merge with v4.4.1; [master comparison](docs/model-comparison.md) |
| 2026-09-12, 21 | Ornith 1.5 9B baseline ROCmFP4, then Abliterated Strix Lean | Baseline llama-bench pp512 990.7, tg64 40.7 t/s; abliterated Hermes gates passed later | Different artifact/gates; [sweep](docs/kanban-2026-09-12.md) · [abliterated](docs/ornith-abliterated-20260921.md) |
| 2026-08–09 | Qwen3.8 27B ROCmFP4 FAST / heretic / cyjin | FAST Czech 20.2 t/s with MTP n-max=2; heretic MTP 18.9 tg64; cyjin 13.3 tg64 | Historical 27B comparisons; [three-arm report](docs/qwen38-27b.md) |
| 2026-08-31 | GLM-5.3-Flash AJ-IQ2_XXS, ROCm vs Vulkan | 14.63 vs 8.57 tok/s decode; 128k KV / 64k Hermes window | ROCm win for this GGUF; [report](docs/glm-53-flash.md) |
| 2026-09-09 | Nex N2.5 Mini ROCmFP4 Strix Lean | llama-bench tg64 81.6 t/s; Czech/EN generation unusable | **Quality rejected** despite speed; [report](docs/nex-n25-mini.md) |
| 2026-09-21 | K2 Horizon 3.7B heretic-xortron / 7B Uno IQ4_XS / 7B ROCmFP4 Strix Lean | No GGUF for 3.7B pinned path; unknown architecture / unsupported tensor type for 7B | **All loader/preflight blocked**, no tok/s result; [three-candidate report](docs/k2-horizon-candidates-20260921.md) |
| 2026-09-21 | MiniCPM5 abliterated Q8_0 / Bonsai 2 27B uncensored | MiniCPM loader/API/tool request pass, ~70k retrieval and full Hermes fail; Bonsai minimal API pass, tool grammar error | **Rejected as Hermes main models**; [same candidate sweep](docs/k2-horizon-candidates-20260921.md) |
| 2026-09-17 | DeepSeek V4.1 Flash Q2, SSD-streamed ds4 ROCm | 7.12 HTTP completion tok/s incl. reasoning (not native decode); 128k inconclusive; no replicated speedup | Mobile game rejected; [single-host report](docs/deepseek-v41-single-strix-halo.md) · [overnight](docs/deepseek-v41-night-20260917.md) · [second pass](docs/deepseek-v41-speed2-20260917.md) |

These methods are **not interchangeable**: `llama-bench` pp/tg, server output decode, request wall time, loader compatibility and Hermes acceptance are distinct gates. [Complete report/evidence index](docs/llm-test-index.md) · [master comparison](docs/model-comparison.md).

## Measured tests and interpretation

### Latest Strata tuning and hotfix validation · 2026-10-06

Prefill tuning improved the 126k-input + 420-output request from **445.30 s** after storage recovery to **109.23 s** in the selected fast configuration. This is a configuration improvement, not an engine speedup from the Python-only v0.1.40.1 hotfix. Depth 2/6 speculation lost at 30k; lookup-chain and MTP Q4 alone did not win whole-request time. Only the selected candidate received three additional independent 30k trials; deep-context figures are single new-prefix samples. A short growing-history retrieval passed with substantial prefix reuse, not a sustained decode result. General coding quality, multi-hour agent stability and a matched current Halogen comparison remain untested.

[Original run and clean retest](docs/strata-v0140-strix-halo-20261006.md) · [Prefill sweep](docs/strata-v0140-optimization-20261006.md) · [Fast-mode combinations](docs/strata-v0140-optimization-followup-20261006.md) · [16384 screening](docs/strata-v0140-optimization-final-20261006.md) · [v0.1.40.1 final matrix](docs/strata-v01401-20261006.md).

## Historical Ornith + uncensored Halogen: bounded coexistence verified

The earlier OOM claim was incorrect: a systemd conflict stopped the other service. After correction both models generated concurrently, including a cold ~62k Halogen prompt and a short Ornith reply on 2026-09-25. Neither a reboot nor a multi-day soak was tested. [Correction and historical 32k data](docs/ornith-halogen-coexistence-correction.md).

## Latest complete HTTP comparison: Gufo PR #91 vs Halogen · 2026-09-28

Official-base Gufo UD-Q4_K_XL on the PR's `strix-llama.cpp` fork **improved over that fork's stock build**, but the current abliterated Halogen HGN+MTP worker won full cold and cached requests at all tested prompt lengths. Cold wall seconds, with 420 output tokens: ~9.5k **31.02 vs 21.71**, ~62k **96.38 vs 66.85**, ~127.5k **181.53 vs 126.11** (Gufo PR vs Halogen). Cached ~127.5k: **19.90 vs 12.83 s**; cold decode **21.15 vs 30.45 tok/s**. Both passed three-marker retrieval. This is one cold and one cached request per depth, not a general quality or uncensored-behavior benchmark. The **native Gufo container** result below (113.47 s cold at ~127.5k) used a different runtime; it is not the PR #91 llama.cpp result. [Full matrix, methods and caveats](docs/gufo-pr91-halogen-e2e-20260928.md) · [raw synthetic responses](records/benchmarks/gufo-pr91-halogen-20260928/).

## Latest LLM measurements: Gufo / CIRU / Halogen · 2026-09-24–25

**Engine-reported output decode tok/s**, cold / cached warm; not request-wall throughput. Same marker-retrieval fixture at long contexts, but **different checkpoints, quantizations and speculation settings**. CIRU short runs used only a 47-token prompt despite an 8k configured slot; do not compare that row as an 8k filled-context test. All completed marker values passed (a narrow retrieval gate, not general quality certification).

| Tested configuration | Short prompt decode | ~62.4k prompt decode | ~127.5k prompt decode | Cold ~62k prefill | Concurrent Ornith |
|---|---:|---:|---:|---:|---|
| **Gufo** official Unsloth UD-Q4_K_XL base, serial/MTP off | 25.74 @9.5k | 22.94 / 22.88–22.89 | 21.05 / 20.98–20.99 | 45.32 s | **Not tested** |
| **CIRU Orca v4.4.1** custom GGUF + PLE + Q8 MTP4 | 30.94 / 36.31 @47 tokens | 17.24 / 19.12 | **Not tested** | 207.87 s | 18.94 short; 13.75 cached ~62k, memory pressure |
| **Uncensored Halogen HGN 0.11.0** abliterated experts + overlay, MTP | 32.91 / 36.96 @9.6k | 31.41 / 34.64 | 30.54 / 33.25–33.26 | 53.05 s | 30.95 cold ~62k; Ornith replied in 1.81 s |

Gufo won **cold ~127.5k request wall time** (113.47 s vs Halogen 125.47 s); Halogen won decode and cached requests. CIRU without MTP: **23.67 / 27.37 tok/s** on the same 47-token short prompt. Its historical **v3 ~3.3 tok/s reject is a different runtime**, not this v4.4.1 result. No CIRU 128k, Gufo+Ornith, reboot or multi-day soak result exists. [Full method, identity, counters and caveats](docs/flash-next-gufo-ciru-halogen-20260925.md) · [raw synthetic API evidence](records/benchmarks/flash-next-september-2026/README.md) · [all LLM reports and failed gates](docs/llm-test-index.md).

## Historical performance reference: native Halogen quality overlay (2026-09-16)

**44.66 tok/s short serving · 41.37 @~32k · 40.08 @~64k · 38.03 @~126k** (MTP decode, prompts actually filled, 256 generated tokens). This was the **aligned quality-profile winner in that historical sweep**, not the uncensored expert-patched worker. Czech with diacritics, sandbox Python, OpenAI tool calls, strict JSON, Responses API and vision OCR passed; serial-vs-MTP byte identity remained under review. Engine is closed source (`halogen-flash-server:0.11.0`). [Exact recipe and evidence](docs/qwen38-halogen.md). Current abliterated worker has a [separate A/B](docs/qwen38-halogen-abliterated.md) and [latest comparison](docs/flash-next-gufo-ciru-halogen-20260925.md).

### DeepSeek V4.1 detail (user stopped the overnight run)

DeepSeek V4.1 Flash Q2 runs on this box via the kyuz0 `ds4` ROCm runtime with SSD expert streaming; measured host portability fix `869a09d`, ROCm 7.2.4, `--ssd-streaming-cache-experts`, `--ctx 8192`, `--batched-session 1`. Exact checkpoint 365,713,686,528 B / SHA-256 `1ce6a8f8806205c…` in the [full report](docs/deepseek-v41-single-strix-halo.md). Game-code trial: the model itself wrote a complete Three.js Tapper-inspired HTML over three attempts (15,316 output tokens, 3,704.68 s model wall). generate02/repair03 passed transport but real desktop/mobile QA rejected the core service/return loop; the owner found the final build unusable on a real phone and **stopped the experiment**. Exact per-attempt data in `records/benchmarks/deepseek-v41-tapper-20260917/measurements.json`. Complete reproducible commands, checksums and every failure: **[docs/deepseek-v41-single-strix-halo.md](docs/deepseek-v41-single-strix-halo.md)**.

### Qwen3.8 Flash-Next (uncensored Orca route) detail

Real-channel series (same repo → Nathanw v0.7.6 → today) measured: code **58.5 t/s** (95% acc) / Czech **30.5 t/s** (70% acc, 2026-09-01) on v0.7.3; Unsloth MIX b10715 slower (25.6 / 42.4) — vendor 1.67× claim is NVIDIA B200, keep Nathanw; matching Uncensored MTP-draft ≈ EasiiX (Czech +5%, 73% vs 66% acc); llama.cpp PR #28136 `on-direct` +10.7% cold prefill only; OrcaRouter Q4_K_M + EasiiX Q8_0 MTP on Nathanw **v0.7.6** Vulkan reaches **35.26 t/s** varied / **27.69 @64k** / **25.89 sustained @~126k**. Uncensored IQ4_XS on Halogen stays loader-blocked (dense `Q5_K` vs required `Q8_0`). All details and exact runlinks: **[docs/qwen38-flash-next.md](docs/qwen38-flash-next.md)**.

### GLM-5.3-Flash detail

Same AJ-IQ2_XXS GGUF, same flags: **ROCm 14.63 t/s vs Vulkan 8.57 t/s** (the ROCm build is the lift, not a quant change). Runs with 128k KV / 64k window. Architectural path is `glm5next` (open PR #27754), so Unsloth MIX build required. Vendor CUDA 3090 11.5 t/s does not transfer. All details: **[docs/glm-53-flash.md](docs/glm-53-flash.md)**.

Every number here was measured on this machine. Forum screenshots, 3090 CUDA,
DGX Spark EXL3, and “128 GB recipe” claims are **not** copied as results.

Separate Hilbert dashboard (publication may lag this README):
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

## Licence

Recipes are MIT. Model weights stay under their own Hugging Face licences.

## All docs

- [00 hardware](docs/00-hardware.md)
- [deepseek v41 night 20260917](docs/deepseek-v41-night-20260917.md)
- [deepseek v41 single strix halo](docs/deepseek-v41-single-strix-halo.md)
- [deepseek v41 speed2 20260917](docs/deepseek-v41-speed2-20260917.md)
- [flash next gufo ciru halogen 20260925](docs/flash-next-gufo-ciru-halogen-20260925.md)
- [gufo pr91 halogen e2e 20260928](docs/gufo-pr91-halogen-e2e-20260928.md)
- [glm 53 flash](docs/glm-53-flash.md)
- [halogen worker 64k](docs/halogen-worker-64k.md)
- [k2 horizon candidates 20260921](docs/k2-horizon-candidates-20260921.md)
- [kanban 2026 09 12](docs/kanban-2026-09-12.md)
- [llm test index](docs/llm-test-index.md)
- [minimax h3](docs/minimax-h3.md)
- [model comparison](docs/model-comparison.md)
- [nex n25 mini](docs/nex-n25-mini.md)
- [ornith abliterated 20260921](docs/ornith-abliterated-20260921.md)
- [ornith halogen coexistence correction](docs/ornith-halogen-coexistence-correction.md)
- [qwen flash next chat and worker](docs/qwen-flash-next-chat-and-worker.md)
- [qwen38 27b](docs/qwen38-27b.md)
- [qwen38 flash next](docs/qwen38-flash-next.md)
- [qwen38 halogen abliterated](docs/qwen38-halogen-abliterated.md)
- [qwen38 halogen](docs/qwen38-halogen.md)
- [signal 38 flash next 2026 09 20](docs/signal-38-flash-next-2026-09-20.md)
- [strata halo orca 20261004](docs/strata-halo-orca-20261004.md)
- [strata v0140 optimization 20261006](docs/strata-v0140-optimization-20261006.md)
- [strata v0140 optimization final 20261006](docs/strata-v0140-optimization-final-20261006.md)
- [strata v0140 optimization followup 20261006](docs/strata-v0140-optimization-followup-20261006.md)
- [strata v0140 strix halo 20261006](docs/strata-v0140-strix-halo-20261006.md)
- [strata v01401 20261006](docs/strata-v01401-20261006.md)
