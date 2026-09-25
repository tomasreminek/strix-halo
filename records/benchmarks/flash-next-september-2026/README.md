# Synthetic API evidence · Flash-Next comparison

[Full English report](../../../docs/flash-next-gufo-ciru-halogen-20260925.md).

This directory contains **32 whitelisted files** copied from local synthetic benchmark artifacts: seven Gufo API responses, eleven Halogen responses, twelve CIRU/Ornith responses, plus Gufo model shard hashes and pinned Hub metadata. `files-manifest.json` records exact byte counts and SHA256 for each. Raw private Hermes session exports, unfiltered server logs and unrelated experiments were deliberately excluded.

- `gufo-5000-1.json`, `gufo-33000-{1,2,3}.json`, `gufo-67500-{1,2,3}.json`: official base Unsloth model via Gufo, serial, no MTP. Generated-token counts and `usage.gufo` fields record prefill/cache/latencies.
- `halogen-{5000,33000,67500}-{1,2,3}.json`: abliterated HGN+overlay with MTP. `halogen-coexist-64k-{halogen,ornith}.json` is the simultaneous cold-prompt control.
- `ciru-8k-short-{1,2}.json`: serial no-MTP; `ciru-8k-mtp-{1,2}.json`: MTP4; `ciru-64k-mtp-b8192-{1,2}.json`: long marker corpus. `ciru-coexist-mtp-{ciru,ornith}.json` and `ciru-coexist-64k-{ciru,ornith}.json`: simultaneous Ornith trials. `ciru-coexist-{ciru,ornith}.json`: no-MTP co-residency diagnostic.
- `fixture-probe.py`: reconstructs the exact marker prompt text using the recorded seed and labels; this is a deterministic corpus generator, not a benchmark server launcher. Run `python3 fixture-probe.py 33000` or `67500` and compare `corpus_sha256`. The body was the same across the three runtimes, but server-side chat templates added different token overhead. The 8k-configured CIRU short test instead used the Czech speed explanation prompt described in the full report.

No `0 tok/s` entry is assigned to aborted attempts. The first CIRU 64k prefill was cancelled at its request timeout with partial progress; it is described in the report, not represented as a completed response. CIRU 128k and Gufo+Ornith were not measured and have no response file. Memory/GTT readings in the report are instantaneous observations, not a continuous peak trace.
