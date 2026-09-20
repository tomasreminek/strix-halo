# Model comparison table · Strix Halo (measured)

Every number here was measured on **Hilbert** (Ryzen AI MAX+ 395 / Radeon 8060S gfx1151, 124 GiB, one GPU job).
Backend and method always stated: `llama-bench` (Vulkan unless noted) or `llama-server print_timing`. Do not mix tables.

## DeepSeek V4.1 Flash Q2 · second pass closed 2026-09-17

**No replicated acceleration certified.** Repeated cache80 pressure aborts qualify the historical recommendation below. Cache24 completed correct extraction/Python/Czech at 17.05372/33.32440/32.19019 seconds, but is a lower-residency fallback, not a speed winner. One exact-output prefix pair was 5.17455s live versus 8.49956s replay; repeated validation aborted, so no general or replicated gain is claimed. Mapped-memory synthetic success failed the full inference gate. Optimization ended early; model-authored game generation and browser QA are separate, still unverified gates.

## DeepSeek V4.1 Flash Q2 · single-Strix-Halo community result 2026-09-17

**User stopped the overnight experiment; no accepted mobile game build.** DeepSeek itself wrote a complete Three.js Tapper-inspired single-HTML game across three attempts: 15,316 completion tokens, 3,704.68 s total request wall, 3.9–4.2 end-to-end completion tok/s (not native decode). generate01 hit the 6,200-token limit without finishing; generate02 produced a complete game that failed real desktop/mobile QA (no customer service/return loop); repair03 completed but the owner rejected it as unplayable on a physical phone. A further DeepSeek-authored mobile repair (repair04, prompt-04-mobile.txt) was requested separately and is not an accepted result. Exact usage/timings ledger: `records/benchmarks/deepseek-v41-tapper-20260917/measurements.json`. QA for a later attempt hit a test-environment WebGL-instantiation blocker, not certified gameplay evidence. [Full measured report, honest outcome and exact guides](deepseek-v41-single-strix-halo.md). [Community summary post](deepseek-v41-community-post.md). Marker: `DEEPSEEK_V41_COMMUNITY_20260917`.

[Full second-pass evidence and caveats](deepseek-v41-speed2-20260917.md). Marker: `DEEPSEEK_V41_SPEED2_20260917`.

## DeepSeek V4.1 Flash Q2 · 2026-09-17 overnight result (historical)

Marker: `DEEPSEEK_V41_NIGHT_20260917`. Separate HTTP task-latency experiment; **do not mix these rates with native decode in the leaderboard**.

Best-supported tested tuple for small coding and Czech chat: exact antirez V4.1 Flash Q2, ds4 baseline + host portability fix `869a09dec445def450bf2d7e6333ced5b9152753`, ROCm 7.2.4/gfx1151, SSD streaming, 80 GiB expert cache, 8192 context, one batched session, default threads, `reasoning_effort: none`. Provisional practical choice, not a universal winner or production promotion.

Three fresh-server repetitions: Python task median 29.21s (first useful answer 13.10s), bugfix 26.41s, Czech 20.41s (first answer 6.96s), JSON 11.49s, extraction 8.42s. Narrow semantic/sandbox tests pass; strict only-code formatting sometimes fails. Native tool-call API remains unverified. Highest finalist median HTTP completion tokens/wall second: **7.12**, on default reasoning (42.69s wall, first useful answer 37.65s); includes reasoning, **not native decode or useful-answer throughput**.

Engine-measured context: 7157/622, 31679/564 and 64461/556 prompt/output tokens; retrieval, sustained output and sandbox coding pass, requested word count fails. Total times 149.28/370.60/687.38s. 128k **INCONCLUSIVE**: calibration timed out at 905.52s, no final answer. MTP/DSpark unsupported; newer runtime and thread variants showed no demonstrated advantage. Cache alternatives had only one ordered trial; natural page-cache effects prevent causal claims.

[Full report, exact identity, commands, caveats and matrix](deepseek-v41-night-20260917.md). No global model/backend change.

## Master leaderboard

| Model (quant) | Backend / runtime | pp512 | pp16k | tg64 / decode | Server decode (prose) | Verdict |
|---|---|---:|---:|---|---|---|
| **Qwen3.8-Flash-Next Abliterated native HGN** | **Halogen 0.11.0 ROCm** · patched experts + 727-tensor overlay | — | — | **40.68** warm 3-prompt mean (36.91–46.20 on sustained rows) | retrieval PASS 8k/16k/32k/60k/123.7k · 2×26.5k PASS | **Preferred main candidate** · no material speed regression; broad quality benchmark still needed |
| **Qwen3.8-Flash-Next native HGN** | **Halogen 0.11.0 ROCm** · quality overlay | — | — | **44.66** short serving | **40.08 @64k · 38.03 @~126k** | **Aligned performance reference** · identity review required |
| **Qwen3.8-Flash-Next Orca Q4_K_M + MTP7** | Nathanw **v0.7.6** Vulkan | — | — | **35.26** varied | **27.69 @64k · 25.89 sustained @126k** | **Uncensored winner / fallback** |
| Qwen3.8-Flash-Next AP-IQ4_XS | Nathanw v0.7.3 Vulkan | 428 | 373 | 30.1 t/s | 29.4–30.5 EN/CZ | Superseded overall winner |
| **Qwen3.8-27B ROCmFP4 FAST** (+MTP n-max 2) | Laurent Vulkan HIP | 61 | 56 | 14.1 | **20.2** CZ (73% acc) | **Full agent winner** (cache-reuse) |
| **Qwen3.8-27B heretic-ara + MTP** | HIP ROCmFPX | 335* | 308* | 14.4 → **18.9** MTP | — | Uncensored worker |
| **Qwen3.8-27B cyjin IQ4_XS** | Nathanw | 334 | 308 | 13.3 | 13.3 | Dropped (slower than heretic) |
| **GLM-5.3-Flash AJ-IQ2_XXS (320B MoE)** | Unsloth MIX ROCm gfx1151 | ~100† | — | **14.63** | 14.4 @128k KV | Big-MoE winner (128k KV on this box) |
| **Signal 3.8-27B AP-Q4_K_XL** | Nathanw v0.7.3 Vulkan0 | **190.9** | **183.1** | **11.9** t/s | 19.3 CZ / 29.2 code (probe) | 2026-09-12 measured · MTP acc 0.60–0.90 |
| **Ornith 1.5-9B Q4_0 ROCMFP4** | Vulkan0 (local build) | **990.7** | **842.8** | **40.7** t/s | 34.2–38.9 (probe) | 2026-09-12 measured · fastest 27B-worker prefill |
| **Nex N2.5-mini ROCmFP4 STRIX_LEAN** | HaloFPX Vulkan0 | 650 | 581 | **81.6** t/s | 78.5 @8k | **Quality REJECT** (CZ/EN garbage; weights deleted) |
| **CIRU-STRIX-Orca (Qwen3.8 Flash)** | CIRU v3 ROCm + PLE + MTP depth-6 | ~24 | — | **3.3** t/s decode · MTP acc 0.25–0.32 | — | **REJECT 2026-09-12** (retest: unusable decode, memory pressure) |

\* cyjin/heretic numbers measured on qwen38-27b.md three-arm control rows.
\† GLM short-prompt prefill ~99–103 t/s (server, Unsloth MIX b10715).

## Detail 2026-09-12 kanban sweep (full numbers)

| Model | llama-bench pp512 (runs) | llama-bench pp16k (runs) | llama-bench tg64 (runs) | API probe prefill/decode (cold, warm, CZ, code, refusal) |
|---|---|---|---|---|
| Signal 3.8-27B AP-Q4_K_XL | 190.9 / 172.4 | 183.1 / 164.8 | 11.88 / 11.18 | 207.6→92.2 / 18.6–29.2 · refused=false |
| Ornith 1.5-9B Q4_0 ROCMFP4 | 990.7 / 694.8 | 842.8 / 560.2 | 40.72 / 36.51 | 750.8→287.6 / 34.2–38.9 · refused=false |
| CIRU-STRIX-Orca | — invalid JSON (bench) — | — | — | partial: 5.8 / 9.5 t/s (1 task) |

Evidence: `records/benchmarks/kanban-2026-09-12/` (bench JSON + probe JSON + server logs; CIRU: ciru-strix-orca-server2.log).

## CIRU-STRIX-Orca retest 2026-09-12 (verdict)

Isolated server (CIRU v3 + PLE + MTP depth-6), n_ctx_slot 262144. Server timings:

| run | prompt eval | decode | draft acceptance |
|---|---|---|---|
| task 0 (593 tok) | 24.10 t/s | 3.26 t/s | 0.32 |
| task 19 (4 tok warm) | 2.96 t/s | 3.40 t/s | 0.25 |
| czech prose (89 tok) | 4.74 t/s | 6.96 t/s | 0.27 |

Decode ~3 t/s with MTP acceptance below 33% — deeper-than-expected draft overhead on RDNA3.5. Two subsequent tasks timed out (cancelled at 40+s + 90+s), server ended memory-pressured (104/24 GiB used). **Rejected for any production chat route**; not merged into any winner table.
