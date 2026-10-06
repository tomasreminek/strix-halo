# Strata v0.1.40 gfx1151 tuning — measured screening

Local draft; not published. Same OrcaRouter Qwen3.8 Flash-Next Uncensored IQ3_XXS model, pinned stock binary and ROCm SDK as the earlier baseline. No chat routing change, no incumbent restoration.

## Screening at 29,999 prompt tokens + 420 completion tokens

- Baseline `--prefill 512`: prefill 313.09 tok/s, decode 42.84 tok/s, request 105.69 s.
- `--prefill 2048`: prefill 549.11 tok/s, decode 42.74 tok/s, request 64.53 s.
- `--prefill auto`: prefill 745.01 tok/s, decode 42.99 tok/s, request 50.11 s.
- Official gfx1151 fast environment, still prefill 512: prefill 341.35 tok/s, decode 43.74 tok/s, request 97.56 s. This changes numerics; it is not a bit-identical quality guarantee.

All 12 screening fixture records passed. Each arm has one new-prefix request and two identical cached repeats; repeats are not independent prefill measurements. The auto path selected 8,192-token chunks with a 96-slot ring, confirmed by engine logs.

## Selected auto configuration validation

- 7,600 prompt + 420 completion tokens: prefill 793.05 tok/s, decode 44.93 tok/s, request 18.95 s.
- 126,000 prompt + 420 completion tokens: prefill 674.68 tok/s, decode 40.93 tok/s, request 197.30 s; cached decode 42.12 and 42.04 tok/s.
- Six validation context records and 17/17 short fixture checks passed. Clean controlled teardown, routing unchanged, both inference ports closed.

At 30k, auto gives 2.38x the measured baseline prefill throughput and 52.59% less request wall time. Against the earlier post-chkdsk 126k baseline (prefill 290.15 tok/s, request 445.30 s), auto gives 2.33x prefill throughput and 55.69% less wall time. These are screening observations, not medians of repeated independent trials. Optimized 64k validation, broader coding quality and long-duration soak remain untested. The official fast switches were not combined with auto in this sweep.

## Evidence and reproducibility

Raw arm configs, engine logs, requests/responses, telemetry and summaries:
`/home/tomasreminek/Projekty/strata-halo-0140/bench/official-halo-20261006/optimization-20261006-120657/`.

Executable controller: `optimization_sweep.py` in the parent benchmark directory. `VERIFIED_COMPARISON.json` preserves the consolidated results and limitations. Only the prefill argument changes for the selected winner; all other runtime settings are inherited from the retained `config-131072.json`. No permanent server/default configuration was adopted.

Systemd's reported memory peak for the outer supervisor is not treated as total GPU/runtime memory; owned child cgroup and host/GTT evidence must be considered separately.
