# Talus v0.1.3 vs Strata 0.1.56 — raw data, 2026-11-04

- `bench_v2.py` — the measurement script (identical for both arms)
- `bench_talus2.json`, `bench_strata2.json` — raw per-depth cells
- `talus-config.json` — the run config used (engine args mirror the production Strata config)

Run: `python3 bench_v2.py <label> http://127.0.0.1:18087 2000,8000,32000,65536`

Method: cold prefill uses a fresh random salt prefix (calibration probes otherwise satisfy the request from
the prefix cache and inflate prefill by ~100×); decode is measured on the warm repeat, 256 greedy tokens,
window from the first to the last content/reasoning delta.

Full write-up: `docs/talus-v013-vs-strata-20261104.md`. Marker `TALUS_013_VS_STRATA_20261104`.
