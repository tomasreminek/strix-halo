# DeepSeek V4.1 Flash Q2 — bounded acceleration second pass

Marker: `DEEPSEEK_V41_SPEED2_20260917`.

## Verdict

No replicated useful acceleration was certified. Optimization is closed, not extended to fill the authorized window. The previous overnight cache80 result remains historical evidence, not a safe universal operating recommendation: repeated second-pass arms hit the active pressure guards. Cache24 completed the short extraction, sandbox Python and reviewed Czech tasks and was selected only as a lower-residency fallback for a separately measured model-authored game. It is **not a speed winner**. The game and browser QA are separate gates and are not certified by this report.

No production route, privileged host setting, model version, quantization, or expert set was changed. Weights and prior evidence were preserved. There is no recommendation to keep the backend resident for manual testing after the game.

## Identity and scope

- Exact DeepSeek V4.1 Flash Q2 GGUF: 365713686528 bytes.
- SHA-256: `1ce6a8f8806205c13330d7ca287bd198331dc5ca35ccc5d8a9a92a188a6f6f42`; unchanged stat/provenance checked against the earlier independent hash.
- Original ds4 baseline plus host portability fix: `869a09dec445def450bf2d7e6333ced5b9152753`.
- ROCm 7.2.4, gfx1151, SSD streaming, context8192, one batched session, default threads, reasoning effort none.
- Natural OS page cache. Short fresh-server and live-session observations are explicitly separated. No controlled cold-cache claim.

## Completed task latency observations

| Arm | Task | Output tokens | Full request wall seconds | Interpretation |
|---|---|---:|---:|---|
| cache80, default16 read workers | first extraction | 11 | 16.59249 | Correct exact JSON |
| cache80, 24 read workers | first extraction | 11 | 16.85011 | Same output; no observed gain |
| cache16 | first extraction | 11 | 19.67628 | Correct, slower observation |
| cache24 | first extraction | 11 | 17.05372 | Correct; lower-residency fallback |
| cache24 | Python first-index | 97 | 33.32440 | Actual sandbox tests pass |
| cache24 | Czech | 111 | 32.19019 | Parent-reviewed two-sentence semantic pass |

The return cache80 baseline pressure-aborted, so reader-pool A/B/A is incomplete. These are single observations, not a causal cache-size ranking. The previous overnight three-trial Python/Czech wall medians were 29.21/20.41 seconds; cache24 is not an acceleration versus those historical results. Native final decode is not certified in these short arms. Output tokens divided by full request wall, if computed, is end-to-end throughput, not decode.

## Prefix reuse: observed but not replicated

The exact same 82-token request produced the same correct 11-token output:

| Regime | Cached prompt tokens | Wall seconds | TTFT seconds |
|---|---:|---:|---:|
| Live continuation | 62 | 5.17455 | 3.76338 |
| Full replay after unrelated RESET | 0 | 8.49956 | 7.57291 |

This is one ordered exploratory pair, confounded by natural expert/page-cache history. The attempted repeated validation pressure-aborted before any completed request. It is not a general decode win or a replicated recommendation. The RESET control correctly returned RESET; its inherited JSON grader was mismatched and was not evidence of a model failure.

## Mechanism evidence and rejected paths

The operative ROCm expert LRU/read implementation is `rocm/ds4_rocm_runtime.cuh`. Async read workers and large expert slabs already exist. Cold cache fill exhibited zero evictions while memory pressure increased; increasing cache84/88 was therefore not justified.

Bounded device-allocation fixtures correlated high-order page depletion, compaction/reclaim and host pageout despite substantial available memory. Owned cgroup RSS/swap does not account for all GPU/GTT memory. This is not proof of ordinary RAM exhaustion or a fully established kernel root cause.

Mapped host expert slabs passed allocation and exact GPU read/write checks; repeated kernel access was similar, but H2D upload was slower. The isolated candidate revision `b6726ab4a337144b5c710943d9a67f28eedc9d5c` pressure-aborted before completing inference. Synthetic success did not transfer into a usable inference win. A mixed device-plus-mapped fixture with process-local THP disabled removed observed compaction but still pressure-aborted. No global THP change, swapoff, cache dropping, remount, or guard relaxation was used to force a win.

Lucebox PR729 was audited. Its V4/DSpark and Qwen27B paths are not interchangeable with V4.1/Engram or Qwen Flash Next. The potentially transferable skip-unused-logits behavior was already present. MTP/DSpark remains unsupported for this exact V4.1 path; no speculative large port was attempted.

The SSD endpoint negotiated PCIe4 x4. This does not establish motherboard Gen5 support. Host IO and temperature telemetry does not justify a claim that an SSD purchase will accelerate this workload, or that thermal throttling was proven.

## Evidence and boundaries

Raw evidence is retained locally under `~/benchmarks/qwen38-acceleration/runs/deepseek-v41-speed2-20260917/`: `optimization-final-matrix.json`, per-arm result/telemetry/native logs, worker reviews, source/build provenance and red/green tests. Guard-aborted arms are INCONCLUSIVE, never zero tokens/s. Private environment dumps are not published.

See [the overnight report](deepseek-v41-night-20260917.md) for the earlier repeated short-task and real-context measurements. No new 64k/128k claim is made here. Actual DeepSeek-authored Tapper generation, repair cost and desktop/mobile browser QA will be reported separately after completion, not inferred from short benchmark correctness.
