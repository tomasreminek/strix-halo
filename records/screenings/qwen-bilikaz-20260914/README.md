# Qwen Orca: bilikaz recipe screening

Read-only live screening; raw evidence in results.json and timings.log. Run `python3 probe.py` with the gguf package available. This is NOT an isolated inference benchmark or an A/B.

## Findings

- Main output.weight is already Q6_K, 521472000 bytes, not BF16.
- MTP sidecar output.weight is Q8_0, 675430400 bytes.
- Therefore the recipe's BF16-to-NVFP4 head speedup does not transfer directly. Lower-bit draft-head experiments require separate artifacts and acceptance/quality gates. No weight files were changed.
- All sampled compaction counters had zero delta during 60.006 seconds of production observation with vm.compaction_proactiveness=20. This does not rule out intermittent compaction at other times, but does not support compaction as the cause of slowdown in this window.
- Swap-in delta: 25 pages; swap-out delta: 0 pages.
- Timings captured from the start of metadata inspection through the end of observation show active decoding; these are overlapping running averages, not independent benchmark runs. No final request timing was captured.

## Blocked / not executed

`sudo -n true` returned 1: a password is required. A/B at compaction values 20 and 0 was NOT performed. No system settings changed, no new inference request sent, no server or game worker stopped.

Output-head kernel profiling, lower-bit head quality/acceptance tests, and PLE alternatives remain unmeasured. Do not infer a throughput improvement from file sizes or the import/read-only probe.
