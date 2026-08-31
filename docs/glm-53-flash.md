# GLM-5.3-Flash on Strix Halo (gfx1151)

**Not a daily driver.** Arch `glm5next` (ggml-org PR [#27754](https://github.com/ggml-org/llama.cpp/pull/27754), still open).
Nathanw / Laurent / ROCmFPX = `unknown architecture`. Use **Unsloth MIX** only.

Measured 2026-08-31 on Ryzen AI MAX+ 395 / 8060S / **124 GiB**.

## Winner

| | |
|---|---|
| Weights | [`aj9o9/GLM-5.3-Flash-GGUF`](https://huggingface.co/aj9o9/GLM-5.3-Flash-GGUF) · `AJ-IQ2_XXS` |
| Size | **87,346,006,560 B (81.35 GiB)** · 2 shards |
| Runtime | Unsloth MIX `b10698-mix` **linux-x64-rocm-gfx1151** |
| Device | `ROCm0: AMD Radeon 8060S Graphics gfx1151` (122880 MiB) |
| Decode | **14.63 t/s** (`llama-server` `print_timing`) |
| llama-bench | pp512 **62.68 ± 0.37** · tg64 **14.53 ± 0.08** · backend **ROCm** |
| Context | 4096 for the smoke (fits; keep Comfy/27B/Flash **off**) |

Same GGUF, same flags, **Vulkan** is slower:

| backend | pp512 | tg64 | server prefill | server decode |
|---|---:|---:|---:|---:|
| Vulkan0 RADV | 60.17 | 8.69 | 24.38 | 8.57 |
| **ROCm0 gfx1151** | **62.68** | **14.53** | **34.52** | **14.63** |

Vulkan flag A/B (threads 4/8/32, ubatch 128–2048, KV q8 vs q4) left decode at **8.51–8.69**.
The lift was the **ROCm tarball**, not another quant.

Czech HTTP 200. Thinking **off**. No MTP (AJ pruned `blk.45`).

## 1. Download the runtime (~336 MiB)

Release: [unslothai/llama.cpp `b10698-mix-67dfc8b`](https://github.com/unslothai/llama.cpp/releases/tag/b10698-mix-67dfc8b)

```bash
MODELS="${MODELS:-$HOME/AI-Models}"
mkdir -p "$MODELS/unsloth-llama-b10698-mix-rocm-gfx1151"
curl -L --fail --retry 8 -C - -o /tmp/unsloth-rocm-gfx1151.tar.gz \
  "https://github.com/unslothai/llama.cpp/releases/download/b10698-mix-67dfc8b/app-b10698-mix-67dfc8b-linux-x64-rocm-gfx1151.tar.gz"
tar -xzf /tmp/unsloth-rocm-gfx1151.tar.gz -C "$MODELS/unsloth-llama-b10698-mix-rocm-gfx1151"
```

Vulkan sibling (same tag, slower on this GGUF):
`app-b10698-mix-67dfc8b-linux-x64-vulkan.tar.gz`

Grep **`libllama.so`** for `glm5next`, not the ~14 kB `llama-server` wrapper.

```bash
ROCM="$MODELS/unsloth-llama-b10698-mix-rocm-gfx1151"
export LD_LIBRARY_PATH="$ROCM"
unset VK_ICD_FILENAMES
"$ROCM/llama-bench" --list-devices
# expect: ROCm0: AMD Radeon 8060S Graphics (122880 MiB, …)
```

## 2. Download AJ-IQ2_XXS (81.35 GiB)

Do **not** start until `stat` matches. Resume with `curl -C -` if HF Xet stalls.

| file | exact bytes |
|---|---:|
| `AJ-IQ2_XXS/GLM-5.3-Flash-AJ-IQ2_XXS-00001-of-00002.gguf` | 44665098240 |
| `AJ-IQ2_XXS/GLM-5.3-Flash-AJ-IQ2_XXS-00002-of-00002.gguf` | 42680908320 |
| **total** | **87346006560** |

```bash
DEST="$MODELS/GLM-5.3-Flash-GGUF/AJ-IQ2_XXS"
mkdir -p "$DEST"
BASE="https://huggingface.co/aj9o9/GLM-5.3-Flash-GGUF/resolve/main/AJ-IQ2_XXS"
# optional: -H "Authorization: Bearer $HF_TOKEN"
curl -L --fail --retry 8 --retry-delay 3 -C - \
  -o "$DEST/GLM-5.3-Flash-AJ-IQ2_XXS-00001-of-00002.gguf" \
  "$BASE/GLM-5.3-Flash-AJ-IQ2_XXS-00001-of-00002.gguf"
curl -L --fail --retry 8 --retry-delay 3 -C - \
  -o "$DEST/GLM-5.3-Flash-AJ-IQ2_XXS-00002-of-00002.gguf" \
  "$BASE/GLM-5.3-Flash-AJ-IQ2_XXS-00002-of-00002.gguf"
stat -c%s "$DEST"/*.gguf
```

Hand-mix notes (author README): 2.18 bpw, `--prune-layers 45`, PPL better than Unsloth UD-IQ1_S.
Author CUDA 3090+64G **11.5 t/s does not transfer**.

## 3. Serve (speed path)

Unload Flash-Next / 27B / Comfy first.

```bash
ROCM="$MODELS/unsloth-llama-b10698-mix-rocm-gfx1151"
MODEL="$MODELS/GLM-5.3-Flash-GGUF/AJ-IQ2_XXS/GLM-5.3-Flash-AJ-IQ2_XXS-00001-of-00002.gguf"
unset VK_ICD_FILENAMES
export LD_LIBRARY_PATH="$ROCM"

"$ROCM/llama-server" -m "$MODEL" \
  --host 127.0.0.1 --port 18090 --alias glm53-flash-aj-iq2 \
  --device ROCm0 --gpu-layers all --flash-attn on --fit off \
  --ctx-size 4096 --batch-size 512 --ubatch-size 128 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --threads 32 --threads-batch 32 \
  --reasoning off --reasoning-budget 0 \
  --jinja --no-webui --metrics --parallel 1 \
  --temp 0.7 --top-p 0.8 --top-k 20
```

Smoke: `GET http://127.0.0.1:18090/health` then `/v1/chat/completions` with
`chat_template_kwargs.enable_thinking=false`. Read **`print_timing`** for decode t/s.

llama-bench (81 GiB **did** run; skip this on 112 GiB IQ3):

```bash
"$ROCM/llama-bench" -m "$MODEL" -p 512 -n 64 -r 2 -ngl -1 \
  -dev ROCm0 -fa on -t 4 -b 512 -ub 128 -o md
```

Vulkan equivalent: `--device Vulkan0` and the vulkan extract dir. Same flags otherwise.

If all-gpu OOMs, ladder (fastest first): all-gpu → `--cpu-moe` (ops GPU) → `--no-kv-offload` → `--no-op-offload` last. On 81 GiB, **all-gpu loaded**. Do not start with `--no-op-offload`.

## 4. Hermes: 128k KV, 64k window (measured 2026-08-31)

Same GGUF + ROCm gfx1151. `n_ctx_slot = 131072` loaded on 124 GiB (~94 GiB used / ~30 GiB available). Decode stayed **~14.4 t/s**. Alias `glm53-flash-aj-iq2`. XOR Flash/27B/Comfy.

| layer | size |
|---|---|
| llama-server `--ctx-size` | **131072** |
| Hermes `model.context_length` (agent window) | **65536** |

### Thinking jinja (not Flash-Next)

Template: `reasoning_effort in ['low','high'] else 'max'`. There is **no** `enable_thinking`. Caps: `supports_reasoning_effort`, tools, preserve-reasoning.

| `reasoning_effort` sent | HTTP | wall | think chars | actual |
|---|---|---:|---:|---|
| **low** | 200 | 4.3 s | ~3 | low |
| **high** | 200 | 7.1 s | 50 | high |
| medium / auto / none / xhigh / max | 200 | 10–16 s | 300–440 | **max** |

`chat_template_kwargs.enable_thinking=false` does **not** stop thinking. Tool-call with `low`: `finish=tool_calls` `get_time` PASS.

Production server (Hermes unit, port 18081):

```bash
"$ROCM/llama-server" -m "$MODEL" \
  --host 127.0.0.1 --port 18081 --alias glm53-flash-aj-iq2 \
  --device ROCm0 --gpu-layers all --flash-attn on --fit off \
  --ctx-size 131072 --batch-size 512 --ubatch-size 128 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --threads 32 --threads-batch 32 \
  --reasoning auto --reasoning-effort high --reasoning-budget 256 \
  --jinja --no-webui --parallel 1 \
  --temp 0.7 --top-p 0.8 --top-k 20
```

Do not send Flash-Next `medium`/`auto` — they become max. Agent without think: client `low` or `--reasoning off`.

## Dead end: Unsloth UD-IQ3_XXS (do not re-download)

112.10 GiB (`120,367,571,715` B). On 124 GiB, community flags

`--gpu-layers all --fit off --cpu-moe --flash-attn off --no-kv-unified`

OOM: radv failed a **1,283,457,024 B** buffer, GTT ~109 GiB, kernel kill.

Only arm that loaded: `--cpu-moe --flash-attn on --no-kv-offload --no-op-offload` ctx 2048 → decode **1.26 t/s**.

## Not a speed path

| thing | why |
|---|---|
| orcarouter Q2_K uncensored (~109 GiB) | same tightness as IQ3; README quality drop; uncensored only |
| Unsloth UD-IQ2_XXS 94.85 GiB | worse fit than aj9o9 81.35 |
| Colibri int4 | different engine, ~195 GB convert, 20–44 s/token |
| EXL3 K2 DGX Spark | NVIDIA GB10 / CUDA 13 / aarch64 — not gfx1151 |
| Nathanw v0.7.2 | no `glm5next` |

Next real lever after 14.6: a **newer Unsloth MIX with fused HC kernels** (prefill). Do not expect Flash-Next 30 t/s from GLM.
