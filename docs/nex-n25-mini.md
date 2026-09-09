# Nex N2.5 Mini ROCmFP4 STRIX_LEAN — Hilbert reject (2026-09-09)

Marker: `nex-n25-hilbert-reject-2026-09-09`

**Speed is real. Usable chat is not.** Do not mix these tok/s into Flash-Next 30 t/s or 27B rows.

Weights were deleted from Hilbert after this write-up. Replicable recipe only.

## Hardware / engine

- Ryzen AI MAX+ 395 · Radeon 8060S · `gfx1151` · 124 GiB unified
- HaloFPX `llama-server` `334f10d81` (11475) · `-dev Vulkan0` · `-fa on` · `-ngl 99`
- ICD: Nathanw `strix-halo-llamacpp-v0.7.3` bundle `radeon_icd.x86_64.json`
- **Trap:** system Mesa ICD → `Available devices: (none)` → silent CPU. Assert `Vulkan` in the llama-bench backend column.

## Weights (deleted locally)

- Hub: [`julianmb/Nex-N2.5-mini-ROCmFP4-GGUF`](https://huggingface.co/julianmb/Nex-N2.5-mini-ROCmFP4-GGUF)
- File: `Nex-N2.5-mini-ROCmFP4-STRIX_LEAN.gguf` · **18,597,336,864 B** · SHA-256 `406c96dbab1994998137e5cf093c4094f9af8be5c1e3268ed6284670bca2d06e`
- Arch: `qwen35moe` 35B.A3B · 34.66 B / ~3 B active · 17.31 GiB

## llama-bench (Vulkan0, 3 reps)

| test | t/s |
|---|---:|
| `pp512` | **650.42 ± 0.18** |
| `pp2048` | 638.12 ± 5.53 |
| `pp8192` | 608.93 ± 2.93 |
| `pp16384` | **580.82 ± 0.78** |
| `tg64` | **81.58 ± 0.55** |

Vendor (same quant, Vulkan): decode 76.92 / pp512 642.37. Hilbert matched that band.

## llama-server

| ctx | load | decode | quality |
|---|---|---:|---|
| 8k, `--reasoning off` | yes | 78.5 t/s (512 tok) | 17×19 CS=`1020`, EN=`33`; Czech/code loops |
| 64k, thinking `high` / deepseek / budget −1 | `n_ctx_slot=65536` | ~79 t/s | **0 content**; all tokens in `reasoning_content` (Chinese loops) |
| 128k, same thinking | `n_ctx_slot=131072`, ~33/91 GiB | 78.8 t/s | same reject |

64k/128k is **capacity**, not speed — same lesson as Flash-Next 128k.

## Verdict

Rejected as a daily / Hermes main model. Fast MoE decode does not override broken generation.

Dashboard card: Hilbert `strix-halo.html#nex-n25`.
