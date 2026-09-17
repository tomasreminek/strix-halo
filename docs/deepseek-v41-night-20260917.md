# DeepSeek V4.1 Flash Q2 — overnight measured report

Status: benchmark phase consolidated. No global route/backend changed. No active inference owner at consolidation. Not an exhaustive search or a production promotion.

## Practical choice

For both small programming jobs and everyday Czech use, the best-supported tested choice is the exact antirez V4.1 Flash Q2, ds4 baseline plus isolated host portability fix 869a09dec445def450bf2d7e6333ced5b9152753, ROCm 7.2.4/gfx1151, SSD streaming, --ssd-streaming-cache-experts 80GB (runtime reports 80 GiB), --ctx 8192, --batched-session 1, default threads, reasoning_effort none for quick answers. Keep reasoning available for harder work; this narrow suite does not prove that none preserves quality on difficult programming. Do not promote as a fully certified Hermes main model: native tool_calls API and successful 128k remain unverified.

Exact checkpoint: 365713686528 bytes; SHA256 1ce6a8f8806205c13330d7ca287bd198331dc5ca35ccc5d8a9a92a188a6f6f42; model repo revision dd8a266f7145edc19e2334b46e19b6821f221dc7. Independent full-file hash evidence was checked against unchanged live stat/provenance. Original pinned runtime 09f12d415bb42efc1887e9330b0aebe9c32902da is preserved; build fixes, SDK provenance, exact commands and binary hashes are in this run directory.

## Performance and quality

# DeepSeek V4.1 Flash Q2 — repeated finalist

Three completed cache80 baseline-hostfix trials. Semantic narrow-suite pass; strict bugfix formatting fails.

| Case | Wall median (range), s | First answer median, s | HTTP completion tokens/wall s, median |
|---|---:|---:|---:|
| python_first | 29.21 (28.95–29.36) | 13.10 | 3.32 |
| bugfix | 26.41 (26.16–26.43) | 15.05 | 3.86 |
| tool_json | 11.49 (11.48–11.57) | 9.16 | 1.74 |
| czech | 20.41 (20.38–20.54) | 6.96 | 5.44 |
| extract | 8.42 (8.38–8.42) | 7.17 | 1.31 |
| python_low | 26.41 (26.39–26.42) | 21.39 | 6.36 |
| python_default | 42.69 (42.59–42.87) | 37.65 | 7.12 |

Fresh server per trial; seven varied cases within suite, identical suite repeated in fixed order. Natural OS/page-cache history; NOT controlled cold-cache or same-session prefix-reuse benchmark.
Exact final-answer hashes identical to reviewed baseline for all 21 completions. Four code cases share first_index family; broader merge-intervals evidence is separate.
Bugfix Markdown fence violates only-code instruction despite correct sandbox-tested code. Tool-shaped JSON is not native tool_calls API certification.
Native progress rates diagnostic only; exact reasoning-token counts and certified final decode unavailable.
Three repeats validate only this finalist, not a randomized three-repeat comparison of every cache/runtime. No universal fastest-model claim.

Three fresh-server finalist trials reproduce all seven exact final answers. Python first-index edge cases/bugfix, tool-shaped JSON, factual extraction and parent-reviewed two-sentence Czech pass semantic checks. The bugfix includes a Markdown fence despite only-code instruction. Four coding cases share one family; separate merge-intervals solutions pass sandbox tests in none/low/default, but none also violates only-code formatting. Generated code ran only in the isolated bwrap harness.

The highest median HTTP completion-token rate in finalist cases is 7.12 tokens/s on default reasoning, but this includes reasoning and is NOT useful-answer throughput or native decode. That request takes 42.69s with first useful answer at 37.65s; it is not the best everyday latency. Exact reasoning-token counts are unavailable. Native server progress averages remain diagnostic, not a certified final throughput headline.

## Alternatives and tuning

Single ordered cache48/cache64/cache80 suite wall sums: 206.98 / 183.88 / 165.22 seconds. Natural page-cache history and one trial for the alternatives prevent causal cache attribution. Cache80 alone has three finalist repeats. Newer local-hostfix runtime a7c284f25f50b1c71bded97942c616efa9277b68 produced identical short answers and similar times; no demonstrated advantage. Threads4/8/16 did not show a material advantage. Generic --prefill-chunk1024 was accepted but does not control the dedicated V4.1 graph; requested-setting diagnostic only, 512 skipped rather than advertising a false tuning win.

MTP and DSpark/pipeline unsupported for this exact V4.1 path; no acceptance/depth speedup claimed. Q4 and other same-version packs failed cheap disk/compatibility gates; no heavyweight extra download. CUDA/EXL3 is not AMD, Halogen Qwen is not DeepSeek. CPU diagnostic and hot-expert research deferred. See matrix.json for all explicit statuses.

## Context and limits

8k allocation: actual prompt7157/output622, total149.28s, first answer73.05s.
32k allocation: actual prompt31679/output564, total370.60s, first answer299.47s.
64k allocation: actual prompt64461/output556, total687.38s, first answer615.95s.
All three pass measured-depth/retrieval/sustained output and sandbox code gates, but fail requested350–400 words (347/306/311). These are calibration/natural-cache measurements, not cold prefill benchmarks or full instruction-compliance passes. Long synthetic repository excerpts are not a real repository-edit benchmark.
128k: INCONCLUSIVE. First calibration logged101699 prompt tokens and reached86016 prefill before the905.52s bounded request timeout, with no final answer. Neither128k pass nor capacity failure nor0tok/s. Prefer8k for responsiveness;32k/64k demonstrably work but have long wait times.

## Resource and safety evidence

Runtime planned cache80 total91.09GiB is an allocation budget, not measured RSS. Finalist sampled host available minimum about22GB; sampled server RSS excludes GPU allocations. Server read-byte deltas about204.5–204.9GB per suite show heavy SSD traffic; host swap activity was nonzero. No controlled cache dropping, privileged tuning, or no-swap claim. Exact resource counters are in finalist-review.json. Larger expert budgets were not attempted with this memory envelope.

All22 no-model harness self-tests pass at worker36. Downloader, original smoke, production18081 and unrelated workloads were not modified by this worker. Reports preserve unsupported and inconclusive arms; no certified universal fastest configuration.


## Exact server invocation and environment

```json
{
  "argv": [
    "/home/tomasreminek/benchmarks/qwen38-acceleration/sources/ds4-rocm-ds41-baseline-hostfix/ds4-server",
    "--rocm",
    "-m",
    "/mnt/c/AI-Models/DeepSeek-V4.1-Flash-Q2/DeepSeek-V4.1-Flash-Q2.gguf",
    "--ssd-streaming",
    "--ssd-streaming-cache-experts",
    "80GB",
    "--ctx",
    "8192",
    "--batched-session",
    "1",
    "--host",
    "127.0.0.1",
    "--port",
    "18095"
  ],
  "environment_overrides": {
    "ROCM_PATH": "/mnt/data/rocm-724-prefix/opt/rocm-7.2.4",
    "HIP_PATH": "/mnt/data/rocm-724-prefix/opt/rocm-7.2.4",
    "LD_LIBRARY_PATH": "/mnt/data/rocm-724-prefix/opt/rocm-7.2.4/lib:/mnt/data/rocm-724-prefix/opt/rocm-7.2.4/lib64:"
  }
}

```

Request temperature 0, streaming chat, reasoning_effort none for quick cases; low/default tested separately. Readiness uses /v1/models (not /health).

## Explicit experiment matrix

# Matrix

- baseline-cache48: MEASURED_PRELIMINARY — Seven complete short answers; narrow sandbox/JSON/extraction gates and exact-hash Czech review PASS. Actual reported cache matches requested budget. See cache-review.json; no finalist or populated-context claim.
- baseline-cache64: MEASURED_PRELIMINARY — Seven complete short answers; narrow sandbox/JSON/extraction gates and exact-hash Czech review PASS. Actual reported cache matches requested budget. See cache-review.json; no finalist or populated-context claim.
- baseline-cache80: MEASURED_PRELIMINARY — All seven complete narrow-suite answers accepted; runtime-reported 80GiB cache. cache-review.json. One trial, natural cache history; no winner or populated-context certification.
- newer-rocm-source: BLOCKED_BUILD_REPAIRABLE — Pinned 40b1f63 compile fails at rocm/ds4_rocm_deepseek4_vision.cuh:239: host call to device-only rsqrtf on ROCm 7.2.4. SDK dependencies now resolved and comprehensive header+link fixture passed. Preserve candidate-build.log; next isolate host sqrt seam, then patch only separately identified local-fix worktree/revision.
- prefill-thread-io: PARTIAL_REQUESTED_PREFILL_NOT_EFFECTIVE — Threads4/8/16 no demonstrated benefit. Requested1024 COMPLETE:7206/562 tokens, sandbox pass,323 words fails. Ineffective generic knob; skip512. worker33-prefill-final-review.json.
- mtp-embedded: BLOCKED — Pinned ds4.c:71473 rejects --mtp unless GLM_DSA or Qwen4 with nextn weights. DeepSeek V4.1 not accepted.
- dspark-external: BLOCKED — docs/MODELS.md:93: DSpark and pipeline unsupported for V4.1; model card forbids V4 Flash drafter substitution
- reasoning-none-low-default: MEASURED_PRELIMINARY — All three modes yielded complete valid code in repaired smoke. Prompts differ, so not matched causal A/B. Reasoning text separately captured; usage does not give reasoning-token counts.
- finalists-3-trials: MEASURED_THREE_TRIALS_WITH_CAVEATS — 21 completed answers across three fresh-server cache80 suites; all hashes equal reviewed baseline. Narrow semantic gates pass; bugfix fence fails strict format. finalist-review.json. Natural cache, not controlled cold or causal all-config comparison.
- context-8k: MEASURED_CONTEXT_PASS_INSTRUCTION_FAIL — Engine prompt 7157, output 622; retrieval/sustained generation and sandbox coding pass. Word count 347 vs requested 350–400 fails. See context-review.json. Not cold-cache measurement.
- context-32k: MEASURED_CONTEXT_PASS_INSTRUCTION_FAIL — Engine prompt 31679, output 564; retrieval/sustained generation and sandbox coding pass. Word count 306 vs requested 350–400 fails. See context-review.json. Not cold-cache measurement.
- context-64k: MEASURED_CONTEXT_PASS_INSTRUCTION_FAIL — Engine prompt 64461, output 556; retrieval/sustained generation and sandbox coding pass. Word count 311 vs requested 350–400 fails. See context-review.json. Not cold-cache measurement.
- context-128k: INCONCLUSIVE — First calibration request timeout after 905.52s; engine-log prompt101699, prefill86016, no final output/usage. NOT 128k pass or capacity failure. worker27-context128k-review.json.
- antirez-v41-q4: BLOCKED — 518596067328 bytes plus joining overhead; target /mnt/c only 90815696896 bytes free during Q2 download; no automatic large download/deletion
- vcruz-v41-quants: BLOCKED — Metadata pinned 58d8ac86298fdf85a2440defee08b1abcad32e45; Q2_K is >264GB, insufficient target free disk. Card runtime WIP contradicts later working-rung text; AMD loader compatibility not established; do not download blindly
- upstream-antirez-head: BLOCKED — Current PR1036 is open/unmerged; generic upstream HEAD not evidence of V4.1 gfx1151 support
- cuda-exl3: BLOCKED — NVIDIA path, not gfx1151 ROCm
- halogen-qwen: EXCLUDED — Not a DeepSeek runtime
- cpu: DIAGNOSTIC_ONLY — Not priority for usable large-model performance
- hot-expert: DEFERRED — Optional after baseline; no dual-R9700 kernel port
- publish-deliver: Publication record maintained in the local mission delivery evidence; not a model experiment.
- newer-rocm-local-hostfix: MEASURED_PRELIMINARY — a7c284f candidate cache80 completed all seven narrow cases with identical answers to baseline. candidate-review-results.json. Wall times similar, no demonstrated speed advantage or finalist certification.
- baseline-local-hostfix: MEASURED_SMOKE_PASS — 869a09dec445def450bf2d7e6333ced5b9152753; exact SHA verified. Seven short cases passed including sandbox coding and parent Czech review. Narrow first_index suite; not finalist or context certification. See smoke-parent-review.json.
- broad-merge-intervals: MEASURED_SEMANTIC_PASS — Three none/low/default interval-merging solutions pass real sandbox edge/exhaustive tests and parent semantic review. worker28-broad-review.json. Same fixed-order prompt, natural cache; not causal reasoning A/B. none includes markdown fence despite only-code request.

Local raw evidence: `~/benchmarks/qwen38-acceleration/runs/deepseek-v41-night-20260916/`. No private prompts or environment dumps published. Marker: `DEEPSEEK_V41_NIGHT_20260917`.
