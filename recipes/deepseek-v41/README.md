# DeepSeek V4.1 Flash on Strix Halo — recipes

Reusable pieces from the single-host DeepSeek V4.1 Flash work. The full report for the 2026-11-01 campaign is [docs/gufo-deepseek-v41-iq1m-20261101.md](../../docs/gufo-deepseek-v41-iq1m-20261101.md); frozen output is in [records/benchmarks/gufo-iq1m-20261101](../../records/benchmarks/gufo-iq1m-20261101/).

| File | Purpose |
|---|---|
| `host-sqrt.patch` | 2026-09-17 host-side `sqrt` fix for the earlier `ds4` path |
| `gufo-ds41-engram-dropin.patch` | **2026-11-01** — 4 files, +327/−82: multi-table Engram reader, `DS41_ENGRAM_SHARDS`, Maya-S metadata fallback, `gguf_reader` shared-Engram widening |
| `fetch-verify-iq1m.sh` | download the five ISTA IQ1_M shards with pinned size + SHA256, up to 3 attempts |
| `run-gufo-iq1m.sh` | one benchmark run: `[STREAM=0\|1] ./run-gufo-iq1m.sh <prompt> <gen> <depth> [args]` |
| `overnight-iq1m.sh` | the full matrix driver: waits for shards, verifies, smoke, QA gate, then the matrix |
| `quality-gate.sh` | three deterministic greedy fixtures; exit 0 if at least 2 of 3 pass |
| `depth-sweep.sh` | 32k/64k/128k × 2 repetitions — the authoritative depth table |
| `speed-delta.sh` | n-delta decode measurement (novel vs copy) that cancels load and prefill |
| `serve-2slot.sh` | `gufo serve -j 2 -c 65536` on port `:18092` in its own scope |
| `parse_bench.py` | parses `gufo bench` output into the result CSV |
| `iq1m-sizes.json` | expected byte size of each IQ1_M shard |

## Two rules that apply to every script here

1. **Always run inside a dedicated scope.** These scripts wrap gufo in `systemd-run --user --scope -p MemoryMax=infinity`. A process started from a cgroup-limited shell inherits the cap, sees ~4 GiB, leaves the expert cache at zero and reports ~5.7 tok/s instead of ~24. This is the single most expensive mistake available on this box.
2. **`--expert-cache-bytes` takes bytes.** `64G` is rejected as an invalid integer; use `68719476736`.

## Applying the patch

```bash
git clone https://github.com/franzmoca/gufo && cd gufo
git checkout feat/ds41
git apply /path/to/recipes/deepseek-v41/gufo-ds41-engram-dropin.patch
```

Then build as described in §1 of the report. Without the patch the runtime loads only a single Engram table and will not accept a backbone whose Engram lives in a different quantization.

## Paths

The scripts assume the layout used on this machine and will need the two variables at the top of each file adjusted elsewhere:

- `R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF` — the weight root
- `~/gufo-iq1m-results` — output directory
- `models/ista-iq1m/` — the six-symlink model directory described in §3 of the report
