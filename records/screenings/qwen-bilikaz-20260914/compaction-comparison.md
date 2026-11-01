# Compaction observation follow-up

User set vm.compaction_proactiveness=0 locally; verified before sampling on 2026-09-14. The 60s read-only observation is in compaction-0.json with engine timing lines in compaction-0-timings.log.

Both the earlier value=20 interval and this value=0 interval show zero changes in all monitored compaction counters. No demonstrated compaction-related speedup. These are unmatched production workloads, NOT a controlled A/B.

Three request-end timing records were observed: decode 30.83, 27.61, 30.45 tokens/s; prefill 206.23, 243.67, 256.65 tokens/s. The first request may begin before the observation window. Do not average these into a matched benchmark or compare to overlapping running averages from the first observation.

Swap-in during the zero interval: 13808 pages, 53.9375 MiB with this host's page size. Swap-out zero. Global counters do not attribute this activity to a particular process or establish the setting caused it.

Restoration attempted with sudo -n sysctl -w vm.compaction_proactiveness=20; denied (password required). Initial readback remained 0. The user subsequently restored the setting locally; independent readback confirmed vm.compaction_proactiveness=20. Restoration is complete; no permanent sysctl configuration was written. No model server restarted and no inference request submitted by this probe.
