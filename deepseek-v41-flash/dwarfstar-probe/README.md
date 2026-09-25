# DwarfStar V4.1 lightweight probe

Upstream: https://github.com/antirez/ds4
Pinned commit: `6e4c285a92a1de11863784b748f196b5d4b88a48`

Executed locally on the Strix Halo host. No checkpoint downloaded, no GPU inference and no production services modified.

## Actual results

All four targets compiled and exited with code 0:

- `make -j2 test-engram`: Engram hashes, history and bounded disk rows PASS.
- `make -j2 test-ssd-cache`: SSD cache sizing PASS. This is NOT a disk bandwidth benchmark.
- `make -j2 test-deepseek41-gguf`: V4.1 disk-only GGUF extent PASS using synthetic fixtures, not the published weights. A pointer-signedness compiler warning was emitted. The invalid-layout diagnostic is part of the negative test.
- `make -j2 test-linux-memory`: Linux nonmovable memory PASS.

Full stdout/stderr is in adjacent logs; machine-readable exits are in results.json.

These checks validate useful CPU-side V4.1 infrastructure, not model generation, ROCm kernels, quality or tokens/s. Upstream docs/MODELS.md at this revision explicitly says V4.1 ROCm and DSpark are not implemented. Keep Qwen Orca as the production worker.

## Reproduce

Clone upstream into a separate scratch directory, checkout the pinned commit, then run the four make targets above. No Python/CUDA environment is needed for these targets. Limit build parallelism to avoid competing with coding workers.

Next meaningful gate: identify and implement missing V4.1 ROCm operations, then run small synthetic GPU correctness checks in an available GPU window. Do not download the full Q2 checkpoint just to repeat these CPU tests.
