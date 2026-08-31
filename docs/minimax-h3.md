# MiniMax H3 on Strix Halo (ROCm / gfx1151)

ComfyUI **0.33.0**, PyTorch **ROCm 7.13**, one GPU job (unload the LLM first).

Native H3 audio only. **No Sage Attention** (GH [Comfy-Org/ComfyUI#15263](https://github.com/Comfy-Org/ComfyUI/issues/15263) — H3 DiT attention becomes noise). No external TTS. Human listening outranks Whisper.

Winner gate we use: image ≥7 **and** audio ≥7.

## Production Czech (human-proven)

**FP8 + Qwen3-VL 32B + Euler/simple 8–11**, no Turbo, no EasyCache, no Spectrum stacked on distill.

| | |
|---|---|
| UNET | `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` · `weight_dtype=default` |
| CLIP | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` · `CLIPLoader(type=minimax)` |
| VAE | video **FP16** + audio **FP32** |
| Sampler | Euler / simple · CFG 1.0 · **8–11 steps** |
| Sigma | `MiniMaxH3SigmaShift` video=12 · audio=3 |
| Canvas | 1280×736 landscape or 576×1024 true 9:16 |

Measured:

| clip | wall | human |
|---|---|---|
| FP8 CZ T2V 3.042s (ComfyUI 0.33.0 smoke) | **10m 55s** | overall **8/10** (image 7, audio 8, Czech 8, lipsync 8) |
| INT8 ConvRot + Euler 15 T2V 5.167s | **36m 57s** | image + audio PASS (quality reference, slow) |
| INT8 I2V 5.167s from approved Krea café still | **41m 30s** | image + audio PASS |

20–25 steps on this chip is a wasted day (45–70 min/clip). Set steps from this table, not from an old script default.

## Downloads

| file | ~size | source |
|---|---|---|
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 21 GB | [Abiray/Minimax-H3-nvfp4-INT4-INT8-Convrot](https://huggingface.co/Abiray/Minimax-H3-nvfp4-INT4-INT8-Convrot) |
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 21 GB | same (quality reference) |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 16 GB | same |
| video VAE fp16 / audio VAE fp32 | 5.2 / 0.6 GB | same |
| FastH3 LoRA (speed candidate) | 1.33 GB | [drozbay/MiniMax-H3-FastH3-Preview-LoRA](https://huggingface.co/drozbay/MiniMax-H3-FastH3-Preview-LoRA) pruned rank 128 fp16 |
| Acc-8Step PDD | 1.37 GB | [alibaba-pai/MiniMax-H3-Acc-LoRAs](https://huggingface.co/alibaba-pai/MiniMax-H3-Acc-LoRAs) `MiniMax-H3-FL2VA-Acc-8Step.safetensors` into `models/pdd_acc/` |

INT4: use **Merserk**, not Abiray (Abiray INT4 was corrupt here).

Place UNET in `models/diffusion_models/`, CLIP in `models/text_encoders/`, VAE in `models/vae/`, LoRA in `models/loras/`.

ComfyUI 0.30.0+ already has `_contiguous_qkv_for_gfx1151` (PR #15421). No manual QKV patch on 0.33.0.

## Speed candidates (faster ≠ winner)

Same still, seed 424242, 576×1024, 76f, 24 fps, 3.75s, 2026-08-29:

| arm | wall | vs 11-step 12.00 min | human |
|---|---:|---:|---|
| Euler/simple 11 | 12.00 min | 1.00× | production Czech |
| Acc PDD nfe=8 | 9.51 min | 1.26× | unusable on that export (ASCII cue without háčky) |
| Acc PDD nfe=6 | **6.33 min** | 1.89× | image 6 · audio 7 · overall 7 — **not a winner** |
| Acc PDD nfe=4 | 5.50 min | 2.18× | **REJECT** metallic echo |
| FastH3 v0.2 LoRA 4-step | **5.67 min** | 2.12× | image 7 · audio 5 · overall 6 — **not a winner** |

Acc is **not** a Turbo LoRA. Node pack: [Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc](https://github.com/Jalen-Brunson/ComfyUI-MiniMax-H3-PDD-Acc). Official Acc file has `proj_out.weight`; Kijai `*_pruned_comfy` does **not** — PDD node rejects it. Do not load Acc with `MiniMaxH3TurboLoRA` or `LoraLoaderModelOnly`. Distill LoRAs do not stack. `nfe=6` is partition `8,8,4,4,4,4` of the **same** 8-step file.

FastH3: `LoraLoaderModelOnly` @ 1.0 on the **same FP8 UNET**, 4 steps euler/simple, CFG 1.0, SigmaShift 12/3. **Do not download** `FastVideo/FastVideo-Minimax-FastH3-Preview-v0.2` (~148 GB). Claimed 14× is 8×B200, not gfx1151.

Write Czech `<d>` cues **with háčky**. Acc speaks the string verbatim.

## Graph sketch (production)

```
UNETLoader(fp8, default)
  → MiniMaxH3SigmaShift(12, 3)
  → MiniMaxH3ImageToVideo or T2V latent
CLIPLoader(qwen3vl_32b, type=minimax) → CLIPTextEncode
KSampler(euler, simple, 8–11, cfg=1.0)
VAEDecode (fp16 video) + VAEDecodeAudio (fp32)
VHS_VideoCombine → AAC MP4
```

I2V: first frame **must** match output resolution. Workflow JSON keys must be **strings**.

## What failed

| approach | why |
|---|---|
| Sage Attention | pure noise |
| Acc nfe=4 | metallic echo |
| Turbo LoRA 4-step (older) | music, no Czech |
| Spectrum blend 0.50 | garbled speech |
| EasyCache 20–25 steps | 40–60+ min, over time limit |
| Studio 1939 strong LoRA | Czech dialogue 4/10 overall, audio 2/10 |
| ClipProj without Turbo | silent no-output |
| LTX 2.5 “no subtitles” | we did **not** get clean Czech frames without subtitle-like text |

Video evidence: [video-benchmark.html](http://hilbertkb.31.97.126.27.sslip.io/video-benchmark.html)
