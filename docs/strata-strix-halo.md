# Strata on Strix Halo — consolidated benchmark report

**Test date: 2026-10-06. Latest tested server: v0.1.40.1; stock HIP engine v0.1.40.** Ryzen AI Max+ 395 / gfx1151, 128 GB class UMA. Model: OrcaRouter Qwen3.8 Flash-Next Uncensored IQ3_XXS.

## Current conclusion

Selected candidate: official gfx1151 fast mode, prefill 16384, MTP4, draft attention window 8192. Three independent 30k-input / 420-output trials: median **1301 tok/s prefill**, **44.33 tok/s decode**, **32.65 s request**. At 126k input / 420 output: **1272 tok/s prefill**, **42.44 tok/s decode**, **109.23 s request**. 39/39 context records and 17/17 short fixtures passed. Server regression suite: 452 tests run, 10 skips, no failures (mock/fake-engine evidence).

Growing history: 126,450 input, 126,420 cached, 27 output tokens in 1.116 s, correct marker retrieval. This is not sustained decode or general programming-quality evidence. Fast mode changes numerics. Multi-file game coding, extended agent-loop soak and a matched current Halogen comparison remain pending. No production routing or permanent worker replacement was made.

This is the single Strata documentation entry. Sections below preserve the chronological experiments, failed attempts, original reboot and recovery, and tuning evidence. **Historical status statements apply to the time of that experiment, not the current verdict above.** Machine-readable measurement summaries are retained under `records/benchmarks/strata-20261006/`.


---

## Strata v0.1.40.1 on Strix Halo — verified results

Server tag v0.1.40.1, commit 82f46a8c8f475f001ad76d92f58f4a4f8ffb0253. Stock HIP engine reused from v0.1.40, as documented by the hotfix release. Model: OrcaRouter Qwen3.8 Flash-Next Uncensored IQ3_XXS; unchanged shards and tokenizer. Fast mode changes numerics; fixture results are not general quality equivalence.

### Completed gates

Server regression suite: 452 tests run, 10 skipped, no failures (mock/fake-engine evidence, not inference speed). 39/39 real context records and 17/17 short quality/tools/JSON fixtures passed.

Selected candidate: official gfx1151 fast environment, prefill 16384, MTP speculation 4, --mtp-window 8192. At 29,999 input + 420 output, three independent-process trials gave medians: prefill 1301.41 tok/s, decode 44.33 tok/s, request 32.65 s. Candidate selection used one screening new-prefix sample per arm; only the selected arm received three additional independent trials. All cached repeats are separately labelled.

Near-128k validation: 126,000 input + 420 output, prefill 1271.86 tok/s, decode 42.44 tok/s, request 109.23 s. Cached decode 43.44 / 43.43 tok/s. Optimized 64k validation also completed: 61,999 input + 420 output, prefill 1314.78 tok/s, decode 42.56 tok/s, request 57.18 s.

Growing-history trial: 126,450 input, 126,420 cached, 27 output tokens, 1.116 s wall time; all three archive markers recalled correctly. Short output is not sustained-decode evidence. Realistic prefix-cache trial was completed even though NEXT_PHASE.json initially retained a stale pending label.

MTP depth 2 and 6 were slower at 30k than control depth 4. Lookup-chain 3 and MTP-q4 all individually did not improve new-request wall time in this corpus; the combination had higher decode but did not beat the selected arm on whole-request time. No causal overall engine speedup is attributed to the Python-only hotfix.

### Lifecycle and monitoring

Completed systemd invocation 3db97b80e5ed44ec8446f88bdc34e3b5, exit 0, runtime 21min 34.538s. No Halogen restoration, no chat routing change. The outer supervisor's reported memory peak is not total GPU/runtime residency.

Raw requests/responses, configs, engine logs, per-arm states, release provenance and HOST_MONITOR.jsonl retained under:
`/home/tomasreminek/Projekty/strata-halo-0140/bench/official-halo-20261006/update01401-20261006-125423/`.

Monitoring includes host memory, swap, diskstats, PSI, VM counters, GPU busy/GTT/VRAM, available hwmon temperature readings and attempted cgroup memory readings. Presence/completeness and peaks must be parsed before claiming exact memory/thermal bounds.

### Still pending

Real multi-file game-coding artifact with tests and visual QA; extended agent-loop soak; a matched current Halogen A/B (not authorized to restore); permanent service activation; publishing to repository and strix-halo.html. Raw measurement matrix: [summary JSON](../records/benchmarks/strata-20261006/strata-v01401-20261006-summary.json).

---

## Strata v0.1.40 on Strix Halo — working test and incident record

Test date: 2026-10-06 (Europe/Prague). **Draft; not published or a stability certification.**

Publication targets after review: the public `tomasreminek/strix-halo` benchmark repository and `strix-halo.html`. Audience: Strix Halo users and Strata maintainers. Preserve failures and blocked follow-up attempts alongside successful measurements.

### Verified independent retest after read-only DATA recovery

The second full run completed with `MATRIX_COMPLETED`, exit status 0, and clean controlled teardown. All 12 filled-context fixture records and all 17 short-suite fixture checks passed. Both model shards and the Strata binary matched the original SHA256 values before testing. No backend was restored; Halogen and Strata ports were closed after completion, and routing remained unchanged. This is a successful bounded lifecycle run, not a reboot/long-duration soak certification.

Actual prompts and decode (new-prefix / cached repeats, tok/s):

- 7,600 tokens: **43.87 / 44.54 / 44.51**.
- 29,999 tokens: **42.88 / 43.48 / 43.47**.
- 61,999 tokens: **41.94 / 42.67 / 42.68**.
- 126,000 tokens: **38.92 / 39.65 / 39.59**.

New-prefix prefill: **327.16 / 311.77 / 301.50 / 290.54 tok/s**, respectively. Each depth request produced 420 completion tokens. Minimum sampled host available memory was **55.41 GiB**; maximum host swap growth was **360,448 bytes**. The systemd completion record reports memory peak **72.1G** and cgroup swap peak **0B**; cgroup peak is not a bound on all GPU/driver allocations.

The DATA volume was mounted with `ro,force` only after system authorization. This enabled testing without writable filesystem repair. **The MFT/MFTMirr inconsistency remains unresolved.** Retest artifacts are isolated under `retry-readonly-20261006/`, leaving the first-run frozen archive intact. [Verified retest summary](../records/benchmarks/strata-20261006/strata-v0140-strix-halo-20261006-retest-summary.json).

### First-run verdict and historical recovery blocker

The retained records show a successful official-HIP build, six kernel checks with exit code 0, and a completed inference matrix at configured context capacities 8,192 / 32,768 / 65,536 / 131,072. The host subsequently rebooted uncleanly. The last persisted controller phase was restoration of the incumbent Halogen backend, **not inference**. This does not establish that either runtime caused the reboot. No overall stability pass is claimed.

Post-reboot Strata-only testing is currently blocked: the DATA NTFS volume containing the model and ROCm SDK did not mount. Kernel evidence says the volume is dirty and recommends `chkdsk`. No forced mount or filesystem repair was performed. Halogen is stopped and its restoration is prohibited by explicit user instruction; chat routing was not changed.

### Build and configuration identity

- Upstream: https://github.com/Niko1221/Strata/releases/tag/v0.1.40
- Strata source: `1735d6471df29b42c26170efaac1f1446a58640f`.
- Preparation record reports no local source patches for the measured build. Later changes are in the external benchmark/lifecycle harness, not engine code.
- Backend / target: HIP / `gfx1151`.
- Official TheRock archive: `therock-dist-linux-gfx1151-7.14.1.tar.gz`.
- Recorded archive SHA256: `c40e8f2bd6630a7d11557c762b99c6fa8afb04c9bd0e51ed1675ee1ca24afb00`.
- Recorded runtime SHA256: `93d983913bf30c645c8dcff3fe82bd6cd949953b49d07d776f4ff30f8d15ea0c`.
- Reused ggml dependency SHA: `3cf03257f219afbe7334045ff7c6a06ac68c627d`.
- Model file requested by loader: `Qwen3.8-Flash-Next-Uncensored-IQ3_XXS-00001-of-00002.gguf`, used for native and PLE inputs, with the Orca IQ3_XXS pack and MTP runtime.
- Key flags: `--mmap-experts --expert-cache auto --prefill 512 --spec 4 --spec-min-p 0.5 --kv int8 --pool-workers 15 --adapt-every 0 --pcie-frac 0 --vram-reserve-mib 3072`.
- API: localhost port 18087, `/v1/chat/completions`; experimental endpoint, not the Telegram default.
- Exact CMake commands, logs, per-context server configs and model identity evidence are retained separately. Build provenance and post-reboot host inventory must not be confused: the latter describes the rebooted machine.

“Uncensored” in the filename and API alias is not, by itself, proof of checkpoint provenance or a general behavioral guarantee. A pinned Hugging Face model-card fetch previously returned HTTP 401. Retain the local model identity manifest and loader evidence, and explicitly resolve this provenance limitation before final publication. Benign non-refusal probes do not establish universal uncensored behavior.

### Measured filled-context results

Each context has one new-prefix request and two identical cached repeats. These are **not three independent cold trials**. All depth records report 420 completion tokens, successful three-marker retrieval and valid decode according to the fixture. The pass predicate is bounded; it is not a broad long-context reasoning benchmark or proof that every prose instruction was followed.

- **8,192 capacity / 7,600 actual prompt tokens:** new-prefix prefill 324.3 tok/s; decode 43.6 tok/s; request wall time 33.08 s. Cached repeat decode approximately 44.0 tok/s.
- **32,768 capacity / 29,999 actual prompt tokens:** new-prefix prefill 312.2 tok/s; decode 41.8 tok/s; request wall time 106.20 s. Cached repeat decode approximately 42.4 tok/s.
- **65,536 capacity / 61,999 actual prompt tokens:** new-prefix prefill 297.4 tok/s; decode 41.5 tok/s; request wall time 218.72 s. Cached repeat decode approximately 42.4 tok/s.
- **131,072 capacity / 126,000 actual prompt tokens:** new-prefix prefill 287.1 tok/s; decode 38.7 tok/s; request wall time 450.05 s. Cached repeat decode approximately 39.4 tok/s.

Numbers above use engine timing fields rounded to one decimal, not request-wall-time output throughput. Cached repeats reuse almost the entire input; their tiny residual-prefill throughput must not be presented as throughput for processing the whole prompt. Full precision, cached-token counts, timestamps and generated content are in raw JSON and the derived summary.

The 8k short suite contains arithmetic, Czech translation and explanation, an executable Python coding check, a tool-call argument validation, structured JSON, varied-output repeats, and two benign non-refusal probes. Fixture pass flags are preliminary evidence, not a substitute for reviewing answer completeness, finish reasons, JSON/schema enforcement and the scope of the coding tests. The original short suite is preserved intact.

### Incident chronology and attribution limits

- 09:20:27 CEST: official preparation starts according to `PREP_STATE.json`.
- 09:25:04 CEST: controller begins the measured matrix according to `RUN_STATE.json`.
- 09:34:28 CEST: the 126,000-token new-prefix request starts.
- 09:42:09 CEST: the final cached repeat starts; the matrix completes before restoration.
- Last persisted controller status: `restoring-incumbent`, with `test_verdict=MATRIX_COMPLETED`.
- Previous-boot Halogen log last recorded weight pinning at approximately 09:42:24 CEST. This is a temporal observation, **not a causal finding**, and does not establish the exact time of the host failure.
- A later boot and unclean journal termination were observed. Retained kernel evidence reviewed so far did not establish a contemporary OOM, kernel panic or GPU reset as the cause.
- Post-reboot mounting of `/mnt/data` fails. Kernel: `ntfs3(nvme0n1p4): volume is dirty and "force" flag is not set!` and a recommendation to use `chkdsk`.
- A Strata-only restart fails before model loading with missing `libhipblaslt.so.1`; the SDK and model are on the unavailable DATA volume. This follow-up is an environmental prerequisite failure, not a new inference result.

The original controller/preparation state remains historical and can look stale. Later policy/incident/blocker records describe the current state; do not overwrite the interrupted state to make the run appear cleanly finished.

### Changes made after the incident

- Created `NO_HALOGEN_RESTORE` and a current-policy record.
- Updated the old restoration harness to omit `qwen38-flashnext.service` when that marker is present.
- Added a systemd condition preventing Halogen from starting while the marker exists. Verified the condition fails; Halogen MainPID is 0.
- Stopped idle ComfyUI for isolated Strata testing; no queued media work was observed.
- Created a separate Strata-only supervisor: no backend restoration, host available-memory floor, swap-growth guard, 96 GiB cgroup memory maximum, and a three-hour residency budget.
- Added mount, SDK and model preflight checks after discovering the unavailable DATA volume. The supervisor is not currently running.

These are lifecycle safety changes, not model/engine performance patches. The dedicated follow-up did not produce successful inference measurements.

### Evidence and publication checklist

The authoritative working evidence is under `strata-halo-0140/bench/official-halo-20261006` on the system disk. Frozen local snapshot: `publication-evidence-20261006-frozen.tar.gz` in that evidence directory, containing 128 evidence files plus `publication-evidence/EVIDENCE_MANIFEST.json`. Archive SHA256: `cf22e67c3b0d05c56c485dee47eccdcbfe88e8225aa69253a8106cdb0b457291`. Every manifest file hash was verified against the compressed snapshot. The original depth fixture reports 12/12 passes and the short fixture 17/17 passes, subject to the limitations above. The [derived JSON summary](../records/benchmarks/strata-20261006/strata-v0140-strix-halo-20261006-summary.json) is stored beside this report; it is not a substitute for full raw requests and responses.

Before publishing the final report and website card:

1. Resolve DATA volume access without silently forcing or repairing the filesystem.
2. Review full answers and fixture limitations; distinguish automated pass flags from human quality assessment.
3. Resolve checkpoint/pack/MTP identity and the uncensored provenance limitation.
4. Quantify original-run memory telemetry, swap growth and available-memory minimum; do not use post-reboot memory as peak-run evidence.
5. Complete an isolated lifecycle/restart check without Halogen restoration if authorized; report its outcome separately.
6. Redact secrets and review archive size/licensing before committing raw evidence publicly.
7. Link report and raw evidence from repository benchmark navigation and both applicable HTML publication targets.
8. Validate, push and read back each target independently. Until then, this remains a local draft, not a live website update.

---

## Strata gfx1151 tuning follow-up — experiment record

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

---

## Strata gfx1151 final configuration screening — experiment record

Stock v0.1.40, Orca Uncensored IQ3_XXS, MTP4, official fast environment retained from the prior follow-up. No production routing or persistent launcher changes.

30k input + 420 output:
- Auto+fast: prefill 1288.88 tok/s, decode 41.69 tok/s, request 33.42 s.
- Fast + prefill 16384: prefill 1303.49 tok/s, decode 42.74 tok/s, request 32.91 s.
- Auto+fast + MTP window 8192: prefill 1285.95 tok/s, decode 42.85 tok/s, request 33.20 s.

Selected prefill16384+fast validation:
- 7,600 input: prefill 1170.49 tok/s, decode 43.72 tok/s, request 16.12 s.
- 61,999 input: prefill 1303.96 tok/s, decode 41.00 tok/s, request 57.94 s.
- 126,000 input: prefill 1270.78 tok/s, decode 40.39 tok/s, request 109.83 s; cached decode 41.30 / 41.25 tok/s.

18/18 depth records, 17/17 short checks passed. Controlled cleanup and unchanged routing verified; ports 18081 and 18087 closed. MTP window arm was screened only at 30k; no deep-context conclusion for that arm.

126k request time improves approximately 2.93% against the prior auto+fast observation (113.14 s). This is a small single-sample difference, not a statistically established gain. 64k decode is lower than the prior auto+fast observation despite slightly better prefill; no universal decode winner is claimed. Fast changes numerics; marker/short fixtures do not establish general quality equivalence. Repeated independent new-prefix samples and broader coding/soak checks remain required before promotion.

Raw evidence: `/home/tomasreminek/Projekty/strata-halo-0140/bench/official-halo-20261006/optimization-final-20261006-123824/`. Executable: `optimization_final.py`; configs and logs retained per arm. Systemd outer-supervisor peak is not GPU memory residency evidence. Not published.

---

## Strata v0.1.40 gfx1151 tuning — measured screening

Historical experiment record. Same OrcaRouter Qwen3.8 Flash-Next Uncensored IQ3_XXS model, pinned stock binary and ROCm SDK as the earlier baseline. No chat routing change, no incumbent restoration.

### Screening at 29,999 prompt tokens + 420 completion tokens

- Baseline `--prefill 512`: prefill 313.09 tok/s, decode 42.84 tok/s, request 105.69 s.
- `--prefill 2048`: prefill 549.11 tok/s, decode 42.74 tok/s, request 64.53 s.
- `--prefill auto`: prefill 745.01 tok/s, decode 42.99 tok/s, request 50.11 s.
- Official gfx1151 fast environment, still prefill 512: prefill 341.35 tok/s, decode 43.74 tok/s, request 97.56 s. This changes numerics; it is not a bit-identical quality guarantee.

All 12 screening fixture records passed. Each arm has one new-prefix request and two identical cached repeats; repeats are not independent prefill measurements. The auto path selected 8,192-token chunks with a 96-slot ring, confirmed by engine logs.

### Selected auto configuration validation

- 7,600 prompt + 420 completion tokens: prefill 793.05 tok/s, decode 44.93 tok/s, request 18.95 s.
- 126,000 prompt + 420 completion tokens: prefill 674.68 tok/s, decode 40.93 tok/s, request 197.30 s; cached decode 42.12 and 42.04 tok/s.
- Six validation context records and 17/17 short fixture checks passed. Clean controlled teardown, routing unchanged, both inference ports closed.

At 30k, auto gives 2.38x the measured baseline prefill throughput and 52.59% less request wall time. Against the earlier post-chkdsk 126k baseline (prefill 290.15 tok/s, request 445.30 s), auto gives 2.33x prefill throughput and 55.69% less wall time. These are screening observations, not medians of repeated independent trials. Optimized 64k validation, broader coding quality and long-duration soak remain untested. The official fast switches were not combined with auto in this sweep.

### Evidence and reproducibility

Raw arm configs, engine logs, requests/responses, telemetry and summaries:
`/home/tomasreminek/Projekty/strata-halo-0140/bench/official-halo-20261006/optimization-20261006-120657/`.

Executable controller: `optimization_sweep.py` in the parent benchmark directory. `VERIFIED_COMPARISON.json` preserves the consolidated results and limitations. Only the prefill argument changes for the selected winner; all other runtime settings are inherited from the retained `config-131072.json`. No permanent server/default configuration was adopted.

Systemd's reported memory peak for the outer supervisor is not treated as total GPU/runtime memory; owned child cgroup and host/GTT evidence must be considered separately.

---

## Strata HIP / Orca IQ3_XXS on Strix Halo — 2026-10-04

Marker: `STRATA_HALO_MEASURED_20261004`.

**Verdict: real inference works, but this configuration is not selected for interactive speed.** This is not a 0 tok/s loader rejection: READY, arithmetic and Czech translation completed, and a separate bounded sample reached64 generated tokens. No promotion of Strata to the Hermes default.

### Exact candidate and preparation

- Ryzen AI MAX+395 / Radeon8060S, gfx1151, 128GiB UMA; isolated ROCm7.2.4 prefix.
- Strata engine0.1.38 at source `99f3dbd0b21d1401b3769e0c0d963913607f380b`. Local build adds gfx1151 to CMake and intrinsic target allowlists; this is an experimental local build, not a claim of upstream Strix-Halo validation.
- `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, revision `e43d00f4e2b8b40b89f75e9adeb1045ac34c8acc`, IQ3_XXS.
- Shard1:44,637,691,008 bytes, SHA256 `aaf57046943c6638480e8984835ce5ec29c486180ff71169d3c22c6929851b7b`.
- Shard2:40,564,977,024 bytes, SHA256 `a19cf9bbe87bce45f312ef11401c88b675f3784c927d02fa2272822229e6a224`.
- Both full hashes match Hub LFS identities. Compatibility pack converts460 small projections to the engine's required form; expert and PLE table source bytes are unchanged. Quantized projections expanded to BF16 do not recover original BF16 accuracy.
- MTP:31 tensors /5,214,301,696 bytes selectively downloaded from pinned base Qwen revision `de4b8e4d43b917e7706784d8bb445c9af86a3540`, all publisher hashes verified. Generated q2_0 MTP GGUF and runtime; the derivative's own target verifies draft proposals.
- Native expert mmap pack:53,477,376,000 bytes. The full pinned host arena caused host-swap growth and was pressure-aborted while RAM remained available; this is INCONCLUSIVE for that allocation arm, not an OOM or speed number. mmap avoids that full pin and completed inference without weakening the guards.
-23 pack conversion tests and10 distinct real-GPU parity/device tests passed. Listing54 ctest entries does not mean all54 were run.

### Serving configuration

8,192 **capacity**, not a filled-context test; int8 KV, prefill128,4096 profile-ranked GPU expert slots (8.30GiB),15 pool workers, MTP spec4/min-p0.5, mmap experts, adaptationoff and PCIe fraction0. The shipped expert profile is used, not a workload-trained optimum. OpenAI requests used greedy temperature0, reasoning_effort none and thinking disabled.

### Measured requests

| Case | Actual prompt / cached | Generated | Prefill s | Decode s | Native decode tok/s | Full wall s | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| arithmetic-repeat | 27 / 20 | 4 | 9.8373 | 16.0604 | 0.2491 | 25.973 | PASS |
| czech-translation | 30 / 0 | 9 | 55.5033 | 27.6232 | 0.3258 | 83.200 | PASS |
| sustained-64 | 32 / 0 | 64 | 61.3622 | 157.0886 | 0.4074 | 218.489 | PASS |

Arithmetic returned `323`; Czech returned `Pes spí pod stromem.` The64-token garden-tip sample is deliberately truncated by its output budget; it is a sustained-generation canary, not a completed eight-tip writing task. Generated counts can include EOS in naturally completed short replies. The64-token sample took218.489s total and157.0886s decode;32/48 draft proposals were accepted.

The earlier tiny CLI READY run generated just2 tokens including EOS, reported0.22tok/s, and is not the sustained result above. CPU browser QA overlapped the API canary; only GPU ownership was exclusive. These one-case observations do not establish an optimized Strata ceiling or a matched comparison against other engines. Do not mix this table into llama-bench or larger-context model rankings.

### Reproduction boundary

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

### Not established and cleanup

No real filled8k,64k or128k prompt, long soak, production-shaped Hermes tool turn, serial/spec byte identity, optimum cache/hipBLAS tuning or matched baseline was tested. Therefore no main-agent qualification and no global route change. Native Strata was stopped after the test; its endpoint/processes were verified gone, and the former Halogen131,072-slot service was restored healthy and idle. Cancelled Dahlia and old Godot controllers were not resurrected. Downloaded weights/pack retained.

[Raw synthetic API requests/responses](../records/benchmarks/strata-halo-20261004/api-results.json) · [machine-readable summary](../records/benchmarks/strata-halo-20261004/summary.json).
