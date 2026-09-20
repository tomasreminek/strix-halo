# Halogen Qwen3.8 Flash-Next Abliterated A/B

**Measured 2026-09-20/21 on AMD Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124 GiB unified memory.**

Candidate: [`Ae55667/halogen-qwen3.8-flash-next-abliterated`](https://huggingface.co/Ae55667/halogen-qwen3.8-flash-next-abliterated), a patch kit for the pinned official Halogen checkpoint. Runtime: `ghcr.io/peonist-ai/halogen-flash-server:0.11.0`.

## Verdict

**Qualified as the preferred main-model candidate.** In this host run it retained the official model's API/MTP/KV behavior, passed every retrieval/context gate, supported two concurrent 65,536-token slots, and delivered warm short decode in the same performance class as the official model. The measured long-prompt wall times were lower for the abliterated run, but page-cache and host-memory fragmentation varied between runs, so this is evidence of no material regression—not a claim of a universal percentage speedup.

Production promotion is intentionally deferred until the current Kanban benchmark queue is complete. The final production configuration should use two slots:

```text
HALOGEN_CTX=65536
HALOGEN_KV_POOL_POSITIONS=131072
HALOGEN_KV_SLOTS=2
HALOGEN_CK_OVERLAY=/ablit/qwen38-flash-next-w4b.overlay.hgn
```

## Artifacts and patch integrity

```text
base checkpoint       124,068,083,904 B
expert_patch.bin       23,634,906,176 B
abliterated overlay     3,506,116,544 B
expert backup          23,634,906,176 B
```

The patcher classified all 49 expert ranges, created a rollback backup, applied the replacement bytes and printed `PATCH APPLIED AND VERIFIED`. The restore script later printed `ORIGINAL EXPERTS RESTORED`; both directions were exercised before the final near-128k comparison.

Startup recognized:

```text
overlay: 727 tensors
99 tensors upgraded to q8g64
MTP available: serial, mtp
```

## Warm short decode

These rows include end-to-end request time and completion-token throughput for identical prompts. The first abliterated request was a cold page-cache outlier and is retained in raw evidence but excluded from the warm comparison.

| prompt | official | abliterated warm |
|---|---:|---:|
| reasoning | 25.02 tok/s | 38.93 tok/s |
| coding | 41.61 tok/s | 46.20 tok/s |
| Czech | 35.39 tok/s | 36.91 tok/s |
| arithmetic mean | **34.01 tok/s** | **40.68 tok/s** |

This small prompt set is a functional A/B, not a statistically complete decode benchmark. Prior official Halogen serving evidence remains the primary throughput reference (44.66 tok/s short, 40.08 at ~64k and 38.03 at ~126k).

## Context retrieval sweep — two-slot production configuration

Every request had unique markers at the beginning and end. `PASS` means both markers were returned exactly.

| prompt tokens | official wall | abliterated wall | official | abliterated |
|---:|---:|---:|---|---|
| 7,875 | 8.25 s | 57.10 s | PASS | PASS |
| 16,037 | 13.23 s | 13.35 s | PASS | PASS |
| 31,997 | 183.30 s | 129.09 s | PASS | PASS |
| 60,077 | 246.74 s | 143.09 s | PASS | PASS |

Wall time includes prefill, page faults and decode. Alternating 124GB checkpoints on a fragmented host produced visible cache variability, so these times must not be mislabeled as pure decode tok/s.

## Dual-slot gate

Configuration: two 65,536-token slots sharing a 131,072-position KV pool.

| test | official | abliterated | result |
|---|---:|---:|---|
| one 48,060-token prompt | 135.89 s | 113.51 s | both exact PASS |
| slot 1, 26,461 tokens | 195.14 s | 156.51 s | both exact PASS |
| slot 2, 26,461 tokens | 195.05 s | 156.60 s | both exact PASS |

The near-identical completion times of the two requests confirm concurrent execution rather than serial queueing.

## Near-128k one-slot gate

For this gate the server was restarted with one 131,072-token slot. Both models received the same 123,679-token prompt and recovered markers from the start and end.

| model | wall time | retrieval |
|---|---:|---|
| official Halogen | 509.18 s | PASS |
| abliterated Halogen | 322.54 s | PASS |

Again, treat wall-time difference as host-run evidence, not a universal speedup claim.

## Caveats

- The ablation direction was recovered from quantized weight differences; upstream reports no broad quality benchmark.
- Removing only the overlay is not a rollback: the 49 expert ranges must also be restored.
- Model startup on this host can spend several minutes compacting fragmented memory. This affected both official and abliterated starts.
- The current test proves performance-class parity, context retrieval, MTP availability and two-slot operation. It does not replace HumanEval, safety or broad language-quality evaluation.

## Evidence

Raw JSON: [`records/benchmarks/qwen38-halogen-abliterated-2026-09-21/`](../records/benchmarks/qwen38-halogen-abliterated-2026-09-21/).
