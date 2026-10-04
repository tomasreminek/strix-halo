# Strata HIP / Orca IQ3_XXS on Strix Halo — 2026-10-04

Marker: `STRATA_HALO_MEASURED_20261004`.

**Verdict: real inference works, but this configuration is not selected for interactive speed.** This is not a 0 tok/s loader rejection: READY, arithmetic and Czech translation completed, and a separate bounded sample reached64 generated tokens. No promotion of Strata to the Hermes default.

## Exact candidate and preparation

- Ryzen AI MAX+395 / Radeon8060S, gfx1151, 128GiB UMA; isolated ROCm7.2.4 prefix.
- Strata engine0.1.38 at source `99f3dbd0b21d1401b3769e0c0d963913607f380b`. Local build adds gfx1151 to CMake and intrinsic target allowlists; this is an experimental local build, not a claim of upstream Strix-Halo validation.
- `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, revision `e43d00f4e2b8b40b89f75e9adeb1045ac34c8acc`, IQ3_XXS.
- Shard1:44,637,691,008 bytes, SHA256 `aaf57046943c6638480e8984835ce5ec29c486180ff71169d3c22c6929851b7b`.
- Shard2:40,564,977,024 bytes, SHA256 `a19cf9bbe87bce45f312ef11401c88b675f3784c927d02fa2272822229e6a224`.
- Both full hashes match Hub LFS identities. Compatibility pack converts460 small projections to the engine's required form; expert and PLE table source bytes are unchanged. Quantized projections expanded to BF16 do not recover original BF16 accuracy.
- MTP:31 tensors /5,214,301,696 bytes selectively downloaded from pinned base Qwen revision `de4b8e4d43b917e7706784d8bb445c9af86a3540`, all publisher hashes verified. Generated q2_0 MTP GGUF and runtime; the derivative's own target verifies draft proposals.
- Native expert mmap pack:53,477,376,000 bytes. The full pinned host arena caused host-swap growth and was pressure-aborted while RAM remained available; this is INCONCLUSIVE for that allocation arm, not an OOM or speed number. mmap avoids that full pin and completed inference without weakening the guards.
-23 pack conversion tests and10 distinct real-GPU parity/device tests passed. Listing54 ctest entries does not mean all54 were run.

## Serving configuration

8,192 **capacity**, not a filled-context test; int8 KV, prefill128,4096 profile-ranked GPU expert slots (8.30GiB),15 pool workers, MTP spec4/min-p0.5, mmap experts, adaptationoff and PCIe fraction0. The shipped expert profile is used, not a workload-trained optimum. OpenAI requests used greedy temperature0, reasoning_effort none and thinking disabled.

## Measured requests

| Case | Actual prompt / cached | Generated | Prefill s | Decode s | Native decode tok/s | Full wall s | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| arithmetic-repeat | 27 / 20 | 4 | 9.8373 | 16.0604 | 0.2491 | 25.973 | PASS |
| czech-translation | 30 / 0 | 9 | 55.5033 | 27.6232 | 0.3258 | 83.200 | PASS |
| sustained-64 | 32 / 0 | 64 | 61.3622 | 157.0886 | 0.4074 | 218.489 | PASS |

Arithmetic returned `323`; Czech returned `Pes spí pod stromem.` The64-token garden-tip sample is deliberately truncated by its output budget; it is a sustained-generation canary, not a completed eight-tip writing task. Generated counts can include EOS in naturally completed short replies. The64-token sample took218.489s total and157.0886s decode;32/48 draft proposals were accepted.

The earlier tiny CLI READY run generated just2 tokens including EOS, reported0.22tok/s, and is not the sustained result above. CPU browser QA overlapped the API canary; only GPU ownership was exclusive. These one-case observations do not establish an optimized Strata ceiling or a matched comparison against other engines. Do not mix this table into llama-bench or larger-context model rankings.

## Reproduction boundary

Use this pinned source and a HIP build for gfx1151. Set process-local LD_LIBRARY_PATH to the verified ROCm7.2.4 prefix and STRATA_GGUF_PY to the build's pinned llama.cpp gguf-py. Prepare with tools/iq_pack.py --compat-bf16 --experts-bin, tools/mtp_fetch.py fetch/verify, tools/mtp_pack.py --experts q2_0, tools/mtp_rt.py, and data/draft_vocab.bin. Native IQ requires MTP speculation, a profile-loaded device residency table and a prefill setting; omitting these is a config failure, not a measured model rejection.

Launch through `python -m serve.server --engine strata --config <config.json> --host 127.0.0.1 --port 18087`. The config args correspond to:

```text
--pack packs/orca-iq3_xxs --native <original first shard>
--ple-gguf <same original first shard> --mmap-experts
--expert-profile data/expert-profile.bin --expert-cache 4096
--prefill 128 --spec 4 --spec-min-p 0.5 --mtp mtp/rt
--max-context 8192 --kv int8 --pool-workers 15
--adapt-every 0 --pcie-frac 0 --vram-reserve-mib 3072
```

The compact notation above describes values; use separate option/value arguments in an actual launcher.

## Not established and cleanup

No real filled8k,64k or128k prompt, long soak, production-shaped Hermes tool turn, serial/spec byte identity, optimum cache/hipBLAS tuning or matched baseline was tested. Therefore no main-agent qualification and no global route change. Native Strata was stopped after the test; its endpoint/processes were verified gone, and the former Halogen131,072-slot service was restored healthy and idle. Cancelled Dahlia and old Godot controllers were not resurrected. Downloaded weights/pack retained.

[Raw synthetic API requests/responses](../records/benchmarks/strata-halo-20261004/api-results.json) · [machine-readable summary](../records/benchmarks/strata-halo-20261004/summary.json).
