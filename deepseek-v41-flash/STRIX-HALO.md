# DeepSeek V4.1 Flash — Strix Halo experiment

This directory is an **experimental AMD Strix Halo port/feasibility spike** based on
[`0xBakeer/deepseek-v41-flash-spark`](https://github.com/0xBakeer/deepseek-v41-flash-spark).

## Current machine

- AMD Ryzen AI MAX+ 395 / Radeon 8060S
- `gfx1151`, 128 GB-class unified memory (124 GiB visible)
- Pop!_OS, Linux x86_64
- ROCm/HIP and Vulkan runtimes; no CUDA / NVIDIA GB10

## Scope of this first pass

- Keep the upstream engine source and documentation locally in this subdirectory.
- Do **not** download the 510 GB checkpoint yet.
- Do **not** claim that the CUDA engine runs on AMD.
- Run dependency-free tests and static portability checks first.
- Isolate the first port target: the FP4 MoE kernel and device abstraction.

## Compatibility verdict (2026-09-14)

**Not runnable on Strix Halo yet.** The upstream recipe is written for NVIDIA GB10 /
`sm_121a`, CUDA 13, CUDA Graphs, and CUDA-specific Triton kernels. The source uses
`torch.cuda` directly in the engine and kernel tests. A real AMD port will need a
ROCm/HIP Triton kernel (or a different AMD kernel), replacement of CUDA Graphs, and
AMD validation of the FP4/UE8M0 layout.

The model checkpoint is approximately 510 GB and the upstream recipe asks for at
least 600 GB local NVMe plus roughly 90 GiB free unified memory at startup. This
experiment deliberately stops before the weight/disk gate.

## Tests run

The following tests do not need the checkpoint or CUDA and are the first acceptance
gate for this directory:

```bash
python3 tools/test_budget.py
python3 tools/test_engine_kwargs.py
python3 tools/test_tune_draw.py
python3 tools/test_atlas_export.py
python3 tools/test_tune_atlas.py
python3 server/test_server.py
python3 tools/strix_halo_probe.py
```

GPU tests remain explicitly separate and must not be reported as passed until an
AMD-compatible kernel exists:

```bash
python3 tools/test_fp4_moe.py
python3 tools/test_cb3_moe.py
```

## Next port gate

1. Add a small device/backend layer instead of hard-coding `"cuda"`.
2. Port or replace `tools/fp4_moe.py` for ROCm `gfx1151`.
3. Run a synthetic FP4 MoE correctness test on Strix Halo without model weights.
4. Measure resident-only kernel bandwidth and memory usage.
5. Only then decide whether freeing disk for the full 510 GB checkpoint is justified.

No production model route, systemd unit, Hermes provider, or Telegram default should
be changed by this experiment.
