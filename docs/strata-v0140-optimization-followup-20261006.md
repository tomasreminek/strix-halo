# Strata gfx1151 tuning follow-up — local draft

Same pinned Strata v0.1.40, Orca Uncensored IQ3_XXS, MTP4 and HIP SDK. Separate 30k screening arms:

- Prefill auto: prefill 748.95 tok/s; decode 43.36 tok/s; request 49.81 s.
- Auto + official fast environment: prefill 1275.94 tok/s; decode 41.75 tok/s; request 33.64 s.
- Auto + --mtp-window 8192: prefill 747.03 tok/s; decode 44.01 tok/s; request 49.77 s. Cached decode 44.90 tok/s; no meaningful fresh-request wall-time advantage demonstrated.

Selected auto+fast validation (each 420 completion tokens):

- 7,600 input: prefill 1198.97; decode 43.87 tok/s; request 15.93 s.
- 61,999 input: prefill 1284.52; decode 43.18 tok/s; request 58.14 s.
- 126,000 input: prefill 1232.26; decode 39.57 tok/s; request 113.14 s. Cached decode 40.58 / 40.56 tok/s.

All 18 depth fixture records and 17/17 short checks passed; all arm lifecycles completed without restoration errors, routing unchanged and inference ports closed. Official fast changes numerics; these gates do not certify unchanged general quality, KL or perplexity. One new-prefix request per arm/depth and two cached repeats are screening evidence, not independent cold-prefill repetitions or a soak test. Auto+fast trades lower decode at 30k and 126k for substantially faster prefill; do not call it the universally best decode configuration.

Fast environment: STRATA_PF_FUSED=1, STRATA_PF_GEMM=1, STRATA_HC_UPMIX=1, STRATA_PA_FAST=1, STRATA_HIP_WMMA=1, STRATA_SELECT_WMMA=1, STRATA_HC_Q8=1, STRATA_PF_SWITCH_MIN_T=4096. --prefill auto; remaining settings inherited from retained baseline. Requested environment switches must not be represented as individually effective without loader/kernel-specific evidence.

Raw configs, logs, requests, responses, telemetry and SUMMARY.json:
`/home/tomasreminek/Projekty/strata-halo-0140/bench/official-halo-20261006/optimization-followup-20261006-122547/`.

No permanent service or chat configuration changed; no publication performed. The supervisor systemd memory peak is not used as total GPU-memory residency evidence.
