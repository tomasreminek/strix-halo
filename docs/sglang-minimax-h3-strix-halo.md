# SGLang MiniMax-H3 on Strix Halo — compatibility gate

**Checked:** 2026-09-21

**Host:** AMD Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124 GiB unified memory

**Verdict:** upstream-blocked on this GPU; no render claimed.

## Requested route

The requested SGLang cookbook URL selects an NVIDIA B200 topology with eight GPUs, Ulysses degree 8, resident native weights and eager lossless T2VA. That topology is not transferable as-is to a single Strix Halo APU.

## Evidence

Inspected `sgl-project/sglang` at commit `f31a7bd45c6ab86796aa012ebfd2378bc42e1a59`:

- `docs/src/snippets/configs/MiniMaxAI/minimax-h3.jsx` lists AMD H3 hardware only as `mi300x` and `mi355x`. `gfx1151` and consumer AMD APUs are absent from `supportedHardware`.
- The same cookbook describes H3 GGUF transformer and text-encoder routes as **CUDA capacity paths**.
- [`sglang` PR #39448](https://github.com/sgl-project/sglang/pull/39448), “Allow MiniMax-H3 full-loop denoise on ROCm,” remains open and unmerged. Its own motivation states that current HIP execution is rejected before denoising because the allowlist lacks `current_platform.is_rocm()`.
- The B200 recipe depends on an eight-GPU CUDA/Ulysses topology and cannot be represented by the single-device `gfx1151` host.

## Local action

No full SGLang checkpoint was downloaded, no runtime was installed into the production environment, and no GPU render was started. A full-model download cannot fix the absent runtime/hardware path and would consume scarce disk without producing a valid gfx1151 test.

The nearest verifiable implementation remains the existing native ComfyUI MiniMax-H3 ROCm stack. This machine already has H3 nodes and locally tested FP8/GGUF/ConvRot/Turbo assets; subsequent H3 cards should run there with local LLM services stopped.

## Retest trigger

Retest SGLang when both conditions are true:

1. ROCm H3 denoising support is merged into a released or pinned upstream revision.
2. A generic ROCm `torch_sdpa`/eager recipe is validated for consumer AMD or specifically `gfx1151`, without requiring MI300/MI355 AITER kernels.

Machine-readable evidence is stored at `records/benchmarks/sglang-minimax-h3-compat-2026-09-21.json`.
