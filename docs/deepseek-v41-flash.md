# Project Maya v1.1.22 / v1.1.23 — DeepSeek V4.1 Flash / Maya-XS

Reference: `strix-halo/deepseek-v41-flash/MAYA-AMD-RESULTS.md`

## Verified
- `v1.1.22` build (`ffe2e5e5`) and `v1.1.23` (`8ceadd7`) on HIP 7.14.1 (`gfx1151`)
- `LD_LIBRARY_PATH=/mnt/data/toolchains/strata-rocm-7.14.1-gfx1151/install/lib` required
- Maya-S pack: `339.5 GB`, SHA `VERSHOVEDNO`, `5` GGUF shards (`IO1_S` `Q2`)
- Maya-XS download: `280.88 GB` (`5` GGUF `276.63 GB` + `dspark` `4.25 GB`), chunked downloader (`19 MB/s`), `11%` complete (`30.77 GB`)
- `Strata` `:18087` disabled; `DSH` `:18095`; `Hermes` active
- Disk freed: `ComfyUI` `87 GB`, `ngram` `48 GB`, `Qwen-Image` `18 GB` → `/mnt/data` `170 GB` free
- CA fix: `pip 26.2.2`, `certifi 2026.10.19` (eMudhra `intermediate` removed)

## Not verified / blocked
- GPU/KFD reset (`amdgpu` `-110`, `/dev/kfd` `EINVAL`) — needs host reboot (user-controlled)
- Maya-S GPU test with `v1.1.22`/`v1.1.23` (reboot required)
- Maya-XS GPU test (download in progress, `dspark` `0%`)
- `v1.1.23` `1.85x` drafting speed claim and HIP attention swizzle
- EXL3 `326.57 GB` load (`self-contained`, `17` shards; `deepseek_v41.py` missing in upstream `exllamav3`)
