# Ornith 1.5 9B Abliterated · main-agent gate · 2026-09-21

> **Correction:** the previous coexistence failure was caused by systemd `Conflicts=ornith.service`, not demonstrated OOM. Both uncensored servers now pass concurrent generation with a 32k Halogen worker slot. See [corrected evidence](ornith-halogen-coexistence-correction.md).


## Candidate

Source: https://huggingface.co/kingjones777/Ornith-1.5-9B-Abliterated-ROCmFP4-GGUF

Selected artifact: `Ornith-1.5-9B-Abliterated-Q4_0_ROCMFP4_STRIX_LEAN.gguf`

- Size: 5,251,556,000 B
- SHA-256: `5793ac31ef0141ea729889e5b633a8071d174504`
- Runtime: `/mnt/data/src/llama-qwen4exp-rocmfpx/build-strix/bin/llama-server`
- Runtime version: `0.3.0-dev`, build 1, commit `510155c`
- Hardware: AMD Ryzen AI MAX+ 395 / Radeon 8060S `gfx1151`, 124 GiB unified memory

The standard PrismML/b10683 loader was rejected for this ROCmFP4 tensor layout (`tensor type 101`); the model passed with the model-specific ROCmFPX/b10715-derived Strix runtime.

## Acceptance gates

| Gate | Result | Evidence |
|---|---|---|
| Loader / API readiness | **PASS** | `/v1/models`, expected alias, `Q4_0_ROCMFP4_STRIX_LEAN` |
| Short exact response | **PASS** | two `ORNITH_SHORT_OK` responses |
| Direct OpenAI tool-call | **PASS** | `get_weather({"city":"Prague"})` |
| Hermes no-tool turn | **PASS** | exact `ORNITH_HERMES_OK` |
| Hermes production-shaped tool loop | **PASS** | time tool called, then `TOOL_LOOP_OK: 16:37:16` |
| Hermes tool loop at 64k slot | **PASS** | `ORNITH_64K_TOOL_OK: 16:40:34` |
| 22.5k retrieval marker | **PASS** | `UNIQUE_ORNITH_MARKER`, 22,523 prompt tokens |
| 64k retrieval marker | **PASS** | `UNIQUE_ORNITH_64K_MARKER`, 63,029 prompt tokens, 104.58 s |
| 128k retrieval marker | **PASS** | `UNIQUE_ORNITH_128K_MARKER`, 117,830 prompt tokens, 265.28 s |

A 70,029-token request against the 65,536 slot was correctly rejected with an explicit context-size error. The 128k run used a real 117,830-token prompt and left generation headroom; server timing was 264.79 s prompt evaluation and 26.34 tok/s for the 12-token answer.

## Production configuration

The persistent `ornith.service` now serves this artifact on `127.0.0.1:18083` with:

```text
-ngl 999 -fa on -c 131072 -np 1
--cache-type-k q8_0 --cache-type-v q8_0
--load-mode mmap --no-host --fit off --jinja --no-webui
--reasoning off
```

Hermes primary configuration:

```text
provider: custom
model: ornith-1.5-9b-abliterated-rocmfp4-strix-lean
base_url: http://127.0.0.1:18083/v1
context_length: 131072
```

The route was verified by reading back `/v1/models`. The Telegram/gateway process requires a fresh `/new` to pick up the new model snapshot.

## Halogen worker coexistence gate

Halogen Qwen Flash Next remains configured as the delegation worker at `127.0.0.1:18081`, but it was **not left running concurrently**. On this 124-GiB UMA host, Halogen startup reserves approximately 92.7 GiB in its normal 2-slot profile and killed the GPU-resident Ornith service. A reduced Halogen coexistence profile (32k request window, 64k KV pool, one slot, trunk pinning disabled) still caused Ornith to be killed. CPU-offloading Ornith is not a valid fallback because this ROCmFP4 quant requires Flash Attention.

Operational decision: keep Ornith as the active main model and keep Halogen stopped until a serialized workload handoff or a separate-memory configuration is available. The worker routing remains configured but is not claimed live.

## Verdict

**PROMOTED as the current local main-agent candidate.** It is the first small uncensored candidate in this sweep to pass loader, direct API, Hermes no-tool, Hermes tool-loop, and real 64k/128k retrieval gates. It is not a claim that two GPU-heavy local servers can safely coexist on this host.
