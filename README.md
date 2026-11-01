# Strix Halo — measured LLM recipes

One box: **AMD Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124.9 GiB unified memory**.
Every number in this repository was measured here. Vendor benchmarks, forum screenshots,
DGX Spark CUDA numbers and "128 GB recipe" claims are **not** copied in as results.

Where things live: **[`docs/`](docs/)** full reports · **[`records/`](records/)** frozen CSVs, logs and raw evidence ·
**[`recipes/`](recipes/)** scripts and patches that reproduce a run · **[`strix-halo.html`](strix-halo.html)** dashboard.

## 1. Hardware

| | |
|---|---|
| CPU / iGPU | AMD Ryzen AI MAX+ 395 · Radeon 8060S · ISA `gfx1151` |
| Memory | 128 GB class unified. Measured `MemTotal` **131,004,904 kB = 124.9 GiB** (`free -h` shows 125Gi). `GTT` **128 GiB**, `VRAM` carveout only **0.5 GiB** — the iGPU maps the same physical RAM, so GTT and RAM do **not** add up. That gap decides whether a 110+ GiB MoE fits. |
| OS | Pop!_OS / Linux 7.0.11, x86_64 · ROCm 7.14.1 toolchain for `gfx1151` |
| Rule | **One GPU-heavy job at a time.** Unload the LLM before ComfyUI and vice versa. |

Four things that silently invalidate a measurement on this box:

- **124.9 GiB, not 128.** A "128 GB" recipe that leaves ~5 GiB after a 112 GiB GGUF OOMs here (extra ~1.28 GiB radv buffer).
- **`MemoryMax` inherits from the caller.** Running a benchmark inside the gateway's cgroup caps it at 24 GiB and turns 24 tok/s into 5.76 tok/s with a 0-byte expert cache. Every run here goes through its own `systemd-run --user --scope -p MemoryMax=infinity`.
- **Prefill and decode are different numbers.** A single "N tok/s" headline is usually a lie.
- **`llama-bench` without a working ICD silently benches the CPU** and still prints plausible tok/s. Assert the backend column.

[Hardware and measurement rules](docs/00-hardware.md)

## 2. Top configurations

Two models are worth running here. Everything else is in the test table below, most of it as a negative result that stops you repeating it.

### Qwen 3.8 Flash-Next — best measured

Three configurations win on three different criteria. Pick by workload, not by the biggest number.

| Configuration | Prefill tok/s | Decode tok/s | Why pick it |
|---|---:|---:|---|
| **Native Halogen `0.11.0`** + aligned quality overlay, MTP, 131k slot | — | **44.66** short · 41.37 @32k · 40.08 @64k · 38.03 @126k | highest decode measured here, best quality/API gate |
| **Strata `v0.1.40.1` + Unsloth UD-IQ4_XS**, MTP4 / window 8192 / lookup 3 | 1189 @7.6k · 1171 @62k · **1294 @126k** | 43.88 @7.6k · 42.13 @62k · **42.71 @126k** | newest run, flattest decode curve; provisional pick for iterative coding |
| **Halogen `0.16.3` + Unsloth UD-IQ4_XS**, native MTP head | **1411 @7.6k · 1674 @62k · 1702 @126k** | 33.84 · 34.40 · 34.98 | highest prefill: a 126k + 420-output request takes **86.22 s** versus Strata **107.46 s** |

Exact configuration behind the decode winner:

- Engine `ghcr.io/peonist-ai/halogen-flash-server:0.11.0`, measured image ID `sha256:7f4036110c6b316d72c3bc534bd5cd88af3078ca1d59fe710f3e342a534d3598` (a registry tag can move — if the ID differs it is a new runtime revision, not this result).
- Weights `qwen38-flash-next-w4b.hgn` + `qwen38-flash-next-w4b.overlay.hgn` + `qwen38-flash-next-vision.hgn`, revision `b8dbb46d03f5d1d0e63b432c2ca763db7e8e0aa4`, SHA256 pinned in the report.
- `HALOGEN_CTX=131072`, `HALOGEN_KV_POOL_POSITIONS=131072`, `HALOGEN_KV_SLOTS=1`, `HALOGEN_MAX_TOK=32768`, `HALOGEN_PROMPT_CACHE=2`, `HALOGEN_VISION_TOWER=1`, `--ipc=host --ulimit memlock=-1:-1`, `/dev/kfd` + `/dev/dri`.
- Practical gate passed: Czech with diacritics, Python parsed and executed, OpenAI tool call, strict JSON schema, Responses API, vision OCR (`ORBIT 4729`).

**Caveat that stays published:** the serial-versus-MTP byte-identity gate failed in every completed serving regime, so the honest status is `COMPLETE_PERFORMANCE_GATE_PASSED_IDENTITY_REVIEW_REQUIRED`. Speed is the selection criterion here, so it is listed as the winner — not reclassified as a pass.

**Uncensored, if that matters more than the last 25 %:** Halogen Abliterated HGN `0.11.0` + patched experts + overlay with MTP gives **32.91 / 36.96 @9.6k · 31.41 / 34.64 @62k · 30.54 / 33.25 @127.5k**, and the OrcaRouter route on Nathanw `v0.7.6` Vulkan reaches **35.26 varied · 27.69 @64k · 25.89 @126k**. Halogen plus OrcaRouter IQ4_XS is loader-blocked: its dense trunk contains `Q5_K` and Halogen requires dense `Q8_0`.

[Exact recipe, provenance and evidence](docs/qwen38-halogen.md) · [Unsloth A/B and Strata comparison](docs/strata-strix-halo.md) · [abliterated worker](docs/qwen38-halogen-abliterated.md) · [raw requests](records/benchmarks/unsloth-20261006/)

### DeepSeek V4.1 Flash 1017 — best measured

A 671B-class MoE at **24 tok/s decode and 1.2–1.3k tok/s prefill on a single Strix Halo**, from a **120.72 GB** IQ1_M backbone plus a **150.21 GiB** Engram taken from a *different* quantization.

| Depth | Prefill tok/s | Decode tok/s |
|---|---:|---:|
| 32,768 | 1264 / 1268 | 23.53 / 23.55 |
| 65,536 | 1198 / 1216 | 23.34 / 23.39 |
| 131,072 | 1142 / 1127 | 22.85 / 22.75 |

Two repetitions per cell, ±2 %. **Context depth is nearly free** — 32k to a full 128k costs 10 % prefill and 3 % decode. Practically: ~1.6 s prefill for 2k tokens, ~8 s for 10k, ~115 s for 128k.

Exact configuration:

- Runtime `franzmoca/gufo` branch `feat/ds41` at `7f8d6430` **plus** the 4-file local patch that makes the Engram drop-in work: [`recipes/deepseek-v41/gufo-ds41-engram-dropin.patch`](recipes/deepseek-v41/gufo-ds41-engram-dropin.patch). HIP `gfx1151`, ROCm 7.14.1, experts streamed from SSD, every run in its own systemd scope.
- Weights: 5 IQ1_M shards (**120.72 GB**, SHA256 pinned) with `DS41_ENGRAM_SHARDS` pointing the two Engram tables at Maya-S shard 6, which already carries them as `Q6_K`. Engram rows are global, not per-shard, so the stock 110.6 GB Engram shard is **never downloaded**.
- Two request slots are a throughput win, not a latency trade: `gufo serve -j 2 -c 65536` gives **24.10 tok/s** at concurrency 1 and **18.88 tok/s per request / 26.16 tok/s aggregate (+36 %)** at concurrency 2, because expert weights are read once per batch (`plan=batched-w2`). One slot for chat, one for a coding worker.
- Prefix cache is the second big lever: TTFT **1.3 ms** on a repeat prompt versus 946 ms cold.
- Prompt lookup is the third: **20.16 tok/s** on novel generation versus **66.32 tok/s** on copy/edit of the prompt (3.3×). Both numbers describe the same model — quote them together.

**Assessment: research runtime, not production.** The quality gate passes **3 of 3** fixtures: arithmetic (391), code (`s[::-1]`) and Czech geography (`Paříž`). The earlier **2 of 3** was a harness artefact, not a weight problem: the gate ran with `--think off`, and V4.1 Flash is a **reasoning model**. `reasoning_effort: none` reproduces the old "Ne" answer, the default answers `Paříž`, and the fixed gate now passes **3 of 3 in 70 s** (evidence in `records/`). Treat it as a fast worker under supervision because the routed experts sit at IQ1_S / IQ1_M / IQ2_XXS — not because a one-word question defeats it. Three paths are closed with evidence: resident weights need **114.00 GiB against 102.21 GiB available**, `--draft-tokens` requires the DFlash2 policy (DSpark `.bin` will not load), and the Maya-S backbone hits a missing `IQ3_S` expert kernel.

[Full replication report, configs and negative results](docs/gufo-deepseek-v41-iq1m-20261101.md) · [patch and scripts](recipes/deepseek-v41/) · [frozen CSVs, logs and manifest](records/benchmarks/gufo-iq1m-20261101/)

**Larger alternative pack:** Project Maya `v1.1.26` on Maya-S (`339.5 GB`) prefills **2.2–2.6× faster** than Maya-XS but decodes slower (15.31 vs 17.0 tok/s at 121k) — a split result, not a clean win. [Report](docs/maya-v1126-20261024.md) · [evidence](records/benchmarks/maya-20261024/)

## 3. All LLM tests · results and evidence

**Historical Orca measurement (weights removed locally on 2026-10-06): OrcaRouter Qwen3.8 Flash-Next Uncensored IQ3_XXS, Strata server v0.1.40.1 / stock v0.1.40 HIP engine, gfx1151 fast mode, prefill 16384, MTP4 with an 8192-token draft attention window.** Verified real 64k/128k context fixtures and bounded lifecycle; **not yet qualified as the long-term game-coding worker**. Fast mode changes numerics. Historical Halogen results use different weights/quantization and are not a current matched A/B. At the latest runtime readback, Strata and Halogen were stopped; no chat routing or permanent worker replacement was made. Dates below are test dates, not release dates.

| Date tested | Model / tested configuration | Measured result or gate | Outcome and full test |
|---|---|---|---|
| **2026-11-01** | **Gufo `feat/ds41` · DeepSeek V4.1 Flash 1017 IQ1_M + Maya-S Q6_K Engram** · `gfx1151`, ROCm 7.14.1, experts streamed, own systemd scope | Depth sweep, 2 rep: **32k 1264/1268 prefill, 23.53/23.55 decode · 64k 1198/1216, 23.34/23.39 · 128k 1142/1127, 22.85/22.75**. Serving `-j 2`: **24.10 tok/s @c=1**, **18.88/request @c=2 = 26.16 aggregate (+36 %)**, prefix-cache TTFT 1.3 ms vs 946 ms. Prompt lookup **20.16 → 66.32 tok/s (3.3×)** | **First usable DeepSeek V4.1 speed on this box**; load 6.46 s, 112.00 GiB backbone + 150.21 GiB Engram. QA gate **2/3** (Czech fixture failed). Resident needs 114.00 vs 102.21 GiB available — unreachable. Research runtime, **not comparable with the `ds4` Q2 rows**. [Report](docs/gufo-deepseek-v41-iq1m-20261101.md) · [logs](records/benchmarks/gufo-iq1m-20261101/) |
| **2026-10-23/24** | **Project Maya v1.1.26 · Maya-S (IQ2 `339.5 GB`, `ntfs3`) / Maya-XS (`258 GB`, `ntfs-3g`)** · `build-hip/maya-ds4`, ROCm 7.14.1 `gfx1151`, `--mmap-experts on --vram-experts 0.5 --max-context 131072 --tp 1`, DSpark drafter | Maya-S prefill **307.1 / 408.8 / 516.4 / 495.8 tok/s**, decode **9.11 / 11.76 / 12.74 / 15.31 tok/s** at **8,037 / 15,524 / 63,526 / 120,867** filled tokens. Maya-XS decode **11.3 / 13.1 / 15.2 / 17.0 tok/s**, prefill **196 / 222 tok/s** at 64k/120k (8k/15.5k withdrawn — warm KV reuse) | **Both packs passed 120k** on the 131,072 slot. Peak cgroup **56.73 GiB (S) / 44.93 GiB (XS)**, GTT 63.67 / 63.82 GiB, `MemAvailable` floor 46.4 / 46.1 GiB, **no freeze / OOM / failed request**. XS decodes ~11 % faster, S prefills 2.2–2.6× faster — split result, neither beats Strata's 36–49 tok/s. XS pack deleted 2026-10-24. [Report](docs/maya-v1126-20261024.md) · [Frozen logs](records/benchmarks/maya-20261024/) |
| **2026-10-06** | **Strata server v0.1.40.1 · Orca Uncensored IQ3_XXS · HIP fast · prefill 16384 · MTP4/window8192** | At **30k**, three independent-process medians: **1301 tok/s prefill / 44.33 tok/s decode / 32.65 s request**. At **126k + 420 output**: **1272 / 42.44 tok/s / 109.23 s**; cached decode **43.43 tok/s**. Growing history: 126,450 input, 126,420 cached, 27 output in **1.12 s** | **39/39 context records, 17/17 short checks passed**; server suite 452 tests, 10 skips, no failures. Clean teardown; multi-file game coding and soak pending. [Report](docs/strata-strix-halo.md) · [JSON](records/benchmarks/strata-20261006/strata-v01401-20261006-summary.json) |
| **2026-10-06** | **Strata v0.1.40 · Orca Qwen3.8 Flash-Next Uncensored IQ3_XXS · HIP gfx1151 + MTP4** | New-prefix decode **43.6 / 41.8 / 41.5 / 38.7 tok/s** at actual **7.6k / 30k / 62k / 126k** prompts; cached **44.0 / 42.4 / 42.4 / 39.4**. New-prefix prefill **324.3 / 312.2 / 297.4 / 287.1 tok/s** | **Historical first run**: inference completed, followed by unclean reboot of unknown cause. Independent retest completed cleanly; NTFS access recovered after Windows chkdsk. Superseded for speed by the tuned row above. [Full report](docs/strata-strix-halo.md) · [machine-readable results](records/benchmarks/strata-20261006/strata-v0140-strix-halo-20261006-summary.json) |
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

### Do not mix tables

- Flash-Next **30 t/s** is a **different model** from 27B (~14–20 t/s) and from GLM (~14.6 t/s).
- PR #28136 `on-direct` is a **cold-prefill SSD-read** delta on AP-IQ4 (+10.7% here), not a decode winner and not the DGX Spark 2–3× claim.
- julianmb/haloq38flash **56 t/s** is Flash-Next **MTP @ 8k**, not GLM. At 128k they report 19–27 t/s — slower than 30 t/s here without MTP.
- GLM **Vulkan 8.57 t/s** is not the Hilbert ceiling. Same GGUF on **ROCm gfx1151** is **14.63 t/s**.
- DeepSeek V4.1 **24 t/s (gufo, IQ1_M, 2026-11-01)** is a different runtime and a different quantization from the **7.12 t/s `ds4` Q2** rows of 2026-09-17. Do not put them in one table, and do not read 24 t/s as an improvement of `ds4`.
- The DeepSeek **bench** number (20.16 t/s novel generation) and the **prompt-lookup** number (66.32 t/s on copy/edit) are the same model in two workloads. Quoting only one of them misrepresents it either way.
- **Nex N2.5 Mini** (HaloFPX Vulkan, 2026-09-09): llama-bench tg64 **81.6 t/s** / pp512 **650**. Quality **reject** (Czech/EN garbage; thinking-on = 0 content). Not a winner. [docs/nex-n25-mini.md](docs/nex-n25-mini.md). Do not mix into Flash 30 t/s.

## 4. All docs (dated)

Newest first. Every report states its own method, quantization and what it does **not** prove.

- **2026-11-01** — [Gufo + DeepSeek V4.1 Flash 1017 IQ1_M](docs/gufo-deepseek-v41-iq1m-20261101.md) — full replication package: build, SHA256 fetch, Engram drop-in, depth sweep, two slots, negative results.
- **2026-11-01** — [Model comparison table](docs/model-comparison.md) — living master table across every runtime tested here.
- **2026-10-24** — [Project Maya v1.1.26 — Maya-S / Maya-XS](docs/maya-v1126-20261024.md) — 339.5 GB versus 258 GB pack, prefill/decode split.
- **2026-10-22** — [Project Maya on AMD Strix Halo — measured results and causal analysis](docs/maya-amd-results.md) — v1.1.21 baseline, GPU-reset causal chain, upstream EXL3 audit (39 KB).
- **2026-10-22** — [EXL3 space plan](docs/exl3-disk-plan.md) — what can be deleted to make room, with sizes.
- **2026-10-11** — [Halogen V2 abliterated · flash_serve 0.18.0](docs/halogen-v2-0180-20261011.md).
- **2026-10-06** — [Strata on Strix Halo — consolidated benchmarks](docs/strata-strix-halo.md) — tuning, hotfix validation, Unsloth UD-IQ4_XS versus Halogen.
- **2026-09-28** — [Gufo PR #91 versus Halogen — complete HTTP requests](docs/gufo-pr91-halogen-e2e-20260928.md).
- **2026-09-25** — [Flash-Next on Hilbert: Gufo, CIRU Orca, Halogen and Ornith](docs/flash-next-gufo-ciru-halogen-20260925.md).
- **2026-09-21** — [LLM test index](docs/llm-test-index.md) — entry point to every report and every failed gate.
- **2026-09-21** — [K2 Horizon candidate sweep](docs/k2-horizon-candidates-20260921.md) — all loader/preflight blocked, no tok/s result.
- **2026-09-21** — [Ornith 1.5 9B Abliterated — main-agent gate](docs/ornith-abliterated-20260921.md).
- **2026-09-21** — [Ornith + Halogen coexistence: correction and live proof](docs/ornith-halogen-coexistence-correction.md).
- **2026-09-21** — [Halogen 64k coding worker alongside Ornith 128k](docs/halogen-worker-64k.md).
- **2026-09-20** — [Signal 3.8 Flash Next + Halogen external-GGUF tests](docs/signal-38-flash-next-2026-09-20.md).
- **2026-09-20** — [Halogen Qwen3.8 Flash-Next Abliterated A/B](docs/qwen38-halogen-abliterated.md).
- **2026-09-19** — [Splitting one Qwen3.8-Flash-Next into a chat model and a working worker](docs/qwen-flash-next-chat-and-worker.md).
- **2026-09-17** — [DeepSeek V4.1 Flash Q2 — overnight measured report](docs/deepseek-v41-night-20260917.md).
- **2026-09-17** — [DeepSeek V4.1 Flash Q2 — bounded acceleration second pass](docs/deepseek-v41-speed2-20260917.md).
- **2026-09-17** — [DeepSeek V4.1 on a single Strix Halo — reproduction and coding verdict](docs/deepseek-v41-single-strix-halo.md).
- **2026-09-16** — [Overall winner: native Halogen Qwen3.8 Flash-Next](docs/qwen38-halogen.md) — the 44.66 tok/s configuration above.
- **2026-09-16** — [Qwen3.8-Flash-Next on Strix Halo](docs/qwen38-flash-next.md) — runtime sweep, Nathanw Vulkan, Orca routes.
- **2026-09-12** — [Kanban benchmark sweep](docs/kanban-2026-09-12.md) — Signal 27B, Ornith baseline, CIRU v3 reject.
- **2026-09-09** — [Nex N2.5 Mini — Hilbert reject](docs/nex-n25-mini.md) — fast, quality unusable.
- **2026-08-31** — [GLM-5.3-Flash on Strix Halo](docs/glm-53-flash.md) — ROCm 14.63 versus Vulkan 8.57 tok/s.
- **2026-08-31** — [Hardware and how we measure](docs/00-hardware.md).
- **2026-08-30** — [Qwen3.8 27B on Strix Halo](docs/qwen38-27b.md) — ROCmFP4 FAST / heretic / cyjin.
- **2026-08-29** — [MiniMax H3 on Strix Halo](docs/minimax-h3.md) — ROCm / `gfx1151`.

Evidence and recipes are not docs: **[`records/`](records/)** holds frozen CSVs, logs and `summary.json` per campaign, **[`recipes/`](recipes/)** holds the runnable scripts and patches.

## Licence

Recipes are MIT. Model weights stay under their own Hugging Face licences.
