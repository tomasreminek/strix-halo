# LLM test index · Hilbert / Strix Halo

Measured results, acceptance gates, and negative experiments. Start with the [master comparison](model-comparison.md) for numbers and the [live page](../strix-halo.html) for the reader-facing dashboard. **Historical recipes are not current service state.** Do not equate `llama-bench`, server decode, request wall time, and Hermes task outcomes.

## Current pair and Flash-Next

- [Ornith 1.5 9B Abliterated](ornith-abliterated-20260921.md): loader, Hermes tool loop, 63k and 117.8k retrieval.
- [Ornith + Halogen coexistence correction](ornith-halogen-coexistence-correction.md): earlier systemd conflict, not proven OOM; historical slot configuration.
- [Halogen 64k worker proof](halogen-worker-64k.md): synthetic code/retrieval and worker policy; 64k setting is historical, current slot is 131,072.
- [Gufo base vs CIRU v4.4.1 Orca vs abliterated Halogen, 24–25 Sep](flash-next-gufo-ciru-halogen-20260925.md): different checkpoint/runtime configurations, 9k/62k/127k and Ornith concurrent controls. [Synthetic response records and fixture](../records/benchmarks/flash-next-september-2026/README.md).
- [Native Halogen reference](qwen38-halogen.md) and [abliterated expert/overlay A/B](qwen38-halogen-abliterated.md): performance, quality and context gates. [Historical native summary](../records/benchmarks/qwen38-halogen-2026-09-16/halogen-native-summary.json) · [abliterated sweep](../records/benchmarks/qwen38-halogen-abliterated-2026-09-21/summary.json).
- [Flash-Next llama.cpp / Orca / AP-IQ4](qwen38-flash-next.md): Nathanw versions, MTP, 64k and 126k. [Chat + worker split](qwen-flash-next-chat-and-worker.md).
- [Signal Flash-Next compatibility](signal-38-flash-next-2026-09-20.md): distinguish loader/schema failures from speed measurements.
- [Worker-context synthetic proof records](../records/benchmarks/worker-context-proof/summary.json).

## Other models and negative gates

- [Qwen3.8 27B](qwen38-27b.md): ROCmFP4 FAST, MTP and heretic/cyjin comparisons.
- [GLM-5.3-Flash](glm-53-flash.md): ROCm vs Vulkan and 128k KV / 64k window.
- [Nex N2.5 Mini](nex-n25-mini.md): fast bench but rejected for Czech/English quality.
- [Kanban 12 Sep: Signal 27B / Ornith / CIRU v3](kanban-2026-09-12.md): historical CIRU v3 result must not be merged with v4.4.1.
- [K2 Horizon 3.7B/7B loader sweep](k2-horizon-candidates-20260921.md): blocked, not speed/quality benchmarks; also records MiniCPM5 and Bonsai gates.
- [DeepSeek V4.1 single-host inference and model-authored game QA](deepseek-v41-single-strix-halo.md), [overnight tasks](deepseek-v41-night-20260917.md), [second-pass speed experiments](deepseek-v41-speed2-20260917.md). [Tapper attempt measurements](../records/benchmarks/deepseek-v41-tapper-20260917/measurements.json). No accepted mobile game build and no certified replicated speedup.
- [DeepSeek V4.1 Flash implementation test report](../deepseek-v41-flash/TEST-REPORT.md) and [DwarfStar CPU-only probe](../deepseek-v41-flash/dwarfstar-probe/README.md): latter is **not GPU inference**.
- [Qwen Orca bilikaz recipe screening](../experiments/qwen-bilikaz/README.md): read-only metadata/compaction observation; no A/B throughput improvement established.

See [hardware and measurement rules](00-hardware.md). The page includes historical inline cards; this index is the entry point to complete reports and evidence. Private operational journals and raw user sessions are intentionally excluded.
