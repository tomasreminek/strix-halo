# Frozen evidence — Gufo + DeepSeek V4.1 Flash 1017 IQ1_M · 2026-11-01

Frozen on 2026-11-01. Every file here is a copy of what a run actually produced; nothing was edited after the fact. The interpretation lives in [docs/gufo-deepseek-v41-iq1m-20261101.md](../../../docs/gufo-deepseek-v41-iq1m-20261101.md).

## Files

| File | Produced by | What it is |
|---|---|---|
| `results.csv` | `overnight-iq1m.sh` | raw matrix rows as the driver wrote them |
| `results_clean.csv` | `parse_bench.py` | deduplicated matrix (latest successful run per config/depth) |
| `summary.txt` | `overnight-iq1m.sh` | matrix table + quality-gate verdict + run notes |
| `quality.txt` | `quality-gate.sh` | three greedy fixtures with the matched answer text |
| `depth-sweep.csv` | `depth-sweep.sh` | 32k/64k/128k, two repetitions each — the authoritative depth table |
| `speed-delta.csv` | `speed-delta.sh` | the four n-delta timing points behind the prompt-lookup figure |
| `speed-probe.txt` | `speed-probe.sh` | single-prompt novel-vs-copy probe with `[Speculative]` counters |
| `serving-2slot.txt` | `gufo-serving-bench.py` | concurrency 1 and 2 against the `-j 2` server |
| `maya_s_removal_manifest.txt` | manual | exact files deleted when 166 GB of Maya-S backbone was reclaimed |
| `raw/depth_<D>_r<N>.log` | `gufo bench` | full bench output for each depth repetition |
| `raw/delta_{novel,copy}_{64,192}.log` | `gufo prompt` | full output for each n-delta timing point |

## Reproduction notes

- Every run was executed inside `systemd-run --user --scope -p MemoryMax=infinity`. Without it the parent cgroup's 24 GiB cap makes the model look ~4× slower and leaves the expert cache at zero — see §4 of the report.
- `depth-sweep.csv` was **regenerated from the saved `raw/depth_*.log` files** after the script's parser was found to write `NA`: the regex expected `pp2048 | 1264.18` while the binary prints `pp2048 @ d32768 | 1264.18`. The fix is in `recipes/deepseek-v41/depth-sweep.sh`. The logs themselves are untouched, so the numbers were re-derived rather than re-measured.
- `speed-delta.csv` contains two `novel,64` rows (24.10 s and 24.05 s). The published 20.16 tok/s uses the 24.05 s point paired with `novel,192` at 30.40 s.
- The `raw/*.log` files are committed deliberately despite the repository-wide `*.log` ignore rule: this directory exists to freeze primary evidence.
- Decode in the `smoke` matrix row is marked invalid on purpose — an 8-token generation measures KV-cache fill, not steady-state decoding.
