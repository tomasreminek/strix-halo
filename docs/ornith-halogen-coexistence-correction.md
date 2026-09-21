# Ornith + Halogen coexistence: correction and live proof

The earlier claim that Halogen OOM-killed Ornith was not supported. `qwen38-flashnext.service` explicitly declared `Conflicts=ornith.service`; the journal records systemd stopping Ornith cleanly. Removing only that conflict allowed both servers to run. The previous CPU attempt failed because quantized V cache was paired with flash attention off, not because CPU inference was proven impossible.

## Verified configuration

- Ornith 1.5 9B Abliterated STRIX_LEAN: GPU, 131072 slot, one slot, Q8 KV, ROCmFPX commit 510155c, localhost 18083.
- Halogen 0.11.0: 32768 request context, 65536-position pool, one slot, pinned trunk ON, 8192 default output, localhost 18081.
- All 49 expert ranges verified already abliterated by vendor patch verifier. Explicit abliterated overlay `/ablit/qwen38-flash-next-w4b.overlay.hgn` selected and mounted read-only.
- Delegation model corrected to the endpoint's actual ID `halogen-qwen3.8-flash-next`.

## Concurrent generation proof

Both requests launched concurrently; each generated 384 tokens. Raw JSON is in `records/benchmarks/ornith-halogen-coexist/`.

Final abliterated worker arm:
- Ornith: 10.116 seconds wall, 38.509 native decode tok/s.
- Halogen: 44.677 seconds wall, 36.913 native decode tok/s; 34.249 seconds prefill/cold-path latency. Decode windows did not fully overlap because Halogen prefilling was slower.
- Both services active after completion.

Prior pinned arm before explicit abliterated overlay selection had overlapping generation: Ornith 13.300 seconds / 29.378 decode tok/s; Halogen 18.919 seconds / 21.765 decode tok/s. Keep this mixed identity arm separate from the final abliterated one.

These are bounded coexistence probes, not a full long-context/concurrency benchmark or a guarantee of indefinite stability. The 384-token caps intentionally truncate long requested lists. Shared GPU compute contention remains; no simultaneous media render was certified. Halogen's worker context is deliberately smaller than Ornith's. The earlier standalone 117830-token Ornith marker result is not a simultaneous deep-context test.

Earlier reports asserting hardware-level impossibility of coexistence are superseded by this correction. No OOM conclusion should be drawn from the previous systemd-conflict experiment.
