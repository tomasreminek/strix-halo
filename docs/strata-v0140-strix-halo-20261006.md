# Strata v0.1.40 on Strix Halo — working test and incident record

Test date: 2026-10-06 (Europe/Prague). **Draft; not published or a stability certification.**

Publication targets after review: the public `tomasreminek/strix-halo` benchmark repository and `strix-halo.html`. Audience: Strix Halo users and Strata maintainers. Preserve failures and blocked follow-up attempts alongside successful measurements.

## Verified independent retest after read-only DATA recovery

The second full run completed with `MATRIX_COMPLETED`, exit status 0, and clean controlled teardown. All 12 filled-context fixture records and all 17 short-suite fixture checks passed. Both model shards and the Strata binary matched the original SHA256 values before testing. No backend was restored; Halogen and Strata ports were closed after completion, and routing remained unchanged. This is a successful bounded lifecycle run, not a reboot/long-duration soak certification.

Actual prompts and decode (new-prefix / cached repeats, tok/s):

- 7,600 tokens: **43.87 / 44.54 / 44.51**.
- 29,999 tokens: **42.88 / 43.48 / 43.47**.
- 61,999 tokens: **41.94 / 42.67 / 42.68**.
- 126,000 tokens: **38.92 / 39.65 / 39.59**.

New-prefix prefill: **327.16 / 311.77 / 301.50 / 290.54 tok/s**, respectively. Each depth request produced 420 completion tokens. Minimum sampled host available memory was **55.41 GiB**; maximum host swap growth was **360,448 bytes**. The systemd completion record reports memory peak **72.1G** and cgroup swap peak **0B**; cgroup peak is not a bound on all GPU/driver allocations.

The DATA volume was mounted with `ro,force` only after system authorization. This enabled testing without writable filesystem repair. **The MFT/MFTMirr inconsistency remains unresolved.** Retest artifacts are isolated under `retry-readonly-20261006/`, leaving the first-run frozen archive intact. [Verified retest summary](strata-v0140-strix-halo-20261006-retest-summary.json).

## First-run verdict and historical recovery blocker

The retained records show a successful official-HIP build, six kernel checks with exit code 0, and a completed inference matrix at configured context capacities 8,192 / 32,768 / 65,536 / 131,072. The host subsequently rebooted uncleanly. The last persisted controller phase was restoration of the incumbent Halogen backend, **not inference**. This does not establish that either runtime caused the reboot. No overall stability pass is claimed.

Post-reboot Strata-only testing is currently blocked: the DATA NTFS volume containing the model and ROCm SDK did not mount. Kernel evidence says the volume is dirty and recommends `chkdsk`. No forced mount or filesystem repair was performed. Halogen is stopped and its restoration is prohibited by explicit user instruction; chat routing was not changed.

## Build and configuration identity

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

## Measured filled-context results

Each context has one new-prefix request and two identical cached repeats. These are **not three independent cold trials**. All depth records report 420 completion tokens, successful three-marker retrieval and valid decode according to the fixture. The pass predicate is bounded; it is not a broad long-context reasoning benchmark or proof that every prose instruction was followed.

- **8,192 capacity / 7,600 actual prompt tokens:** new-prefix prefill 324.3 tok/s; decode 43.6 tok/s; request wall time 33.08 s. Cached repeat decode approximately 44.0 tok/s.
- **32,768 capacity / 29,999 actual prompt tokens:** new-prefix prefill 312.2 tok/s; decode 41.8 tok/s; request wall time 106.20 s. Cached repeat decode approximately 42.4 tok/s.
- **65,536 capacity / 61,999 actual prompt tokens:** new-prefix prefill 297.4 tok/s; decode 41.5 tok/s; request wall time 218.72 s. Cached repeat decode approximately 42.4 tok/s.
- **131,072 capacity / 126,000 actual prompt tokens:** new-prefix prefill 287.1 tok/s; decode 38.7 tok/s; request wall time 450.05 s. Cached repeat decode approximately 39.4 tok/s.

Numbers above use engine timing fields rounded to one decimal, not request-wall-time output throughput. Cached repeats reuse almost the entire input; their tiny residual-prefill throughput must not be presented as throughput for processing the whole prompt. Full precision, cached-token counts, timestamps and generated content are in raw JSON and the derived summary.

The 8k short suite contains arithmetic, Czech translation and explanation, an executable Python coding check, a tool-call argument validation, structured JSON, varied-output repeats, and two benign non-refusal probes. Fixture pass flags are preliminary evidence, not a substitute for reviewing answer completeness, finish reasons, JSON/schema enforcement and the scope of the coding tests. The original short suite is preserved intact.

## Incident chronology and attribution limits

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

## Changes made after the incident

- Created `NO_HALOGEN_RESTORE` and a current-policy record.
- Updated the old restoration harness to omit `qwen38-flashnext.service` when that marker is present.
- Added a systemd condition preventing Halogen from starting while the marker exists. Verified the condition fails; Halogen MainPID is 0.
- Stopped idle ComfyUI for isolated Strata testing; no queued media work was observed.
- Created a separate Strata-only supervisor: no backend restoration, host available-memory floor, swap-growth guard, 96 GiB cgroup memory maximum, and a three-hour residency budget.
- Added mount, SDK and model preflight checks after discovering the unavailable DATA volume. The supervisor is not currently running.

These are lifecycle safety changes, not model/engine performance patches. The dedicated follow-up did not produce successful inference measurements.

## Evidence and publication checklist

The authoritative working evidence is under `strata-halo-0140/bench/official-halo-20261006` on the system disk. Frozen local snapshot: `publication-evidence-20261006-frozen.tar.gz` in that evidence directory, containing 128 evidence files plus `publication-evidence/EVIDENCE_MANIFEST.json`. Archive SHA256: `cf22e67c3b0d05c56c485dee47eccdcbfe88e8225aa69253a8106cdb0b457291`. Every manifest file hash was verified against the compressed snapshot. The original depth fixture reports 12/12 passes and the short fixture 17/17 passes, subject to the limitations above. The [derived JSON summary](strata-v0140-strix-halo-20261006-summary.json) is stored beside this report; it is not a substitute for full raw requests and responses.

Before publishing the final report and website card:

1. Resolve DATA volume access without silently forcing or repairing the filesystem.
2. Review full answers and fixture limitations; distinguish automated pass flags from human quality assessment.
3. Resolve checkpoint/pack/MTP identity and the uncensored provenance limitation.
4. Quantify original-run memory telemetry, swap growth and available-memory minimum; do not use post-reboot memory as peak-run evidence.
5. Complete an isolated lifecycle/restart check without Halogen restoration if authorized; report its outcome separately.
6. Redact secrets and review archive size/licensing before committing raw evidence publicly.
7. Link report and raw evidence from repository benchmark navigation and both applicable HTML publication targets.
8. Validate, push and read back each target independently. Until then, this remains a local draft, not a live website update.
