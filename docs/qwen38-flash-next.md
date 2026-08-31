# Qwen3.8-Flash-Next on Strix Halo

**Winner 2026-08-30** for idle-GPU chat / lite worker.

Not a full-skill Hermes daily driver: qwen4exp **disables** `--cache-reuse` and `--context-shift`
even when you pass them. 27B is still the agent path with persistent KV.

Exclusive ~84–103 GiB. Stop 27B and Comfy first.

## Winner numbers

Runtime: [Nathanw1014/strix-halo-llamacpp](https://github.com/Nathanw1014/strix-halo-llamacpp) **v0.7.2** portable Vulkan
(`ad914eb6` / b10639). Device line: `RADV STRIX_HALO | fp16: dot2 | int dot: 1 | fp4: 0`.

Weights: [`agentionai/Qwen3.8-Flash-Next-AP-GGUF`](https://huggingface.co/agentionai/Qwen3.8-Flash-Next-AP-GGUF)
`AP-IQ4_XS/Qwen3.8-Flash-Next-AP-IQ4_XS.gguf` · **90,447,294,368 B** (84.23 GiB) · `qwen4exp A3B IQ4_NL - 4.5 bpw`.

| test | t/s |
|---|---:|
| llama-bench `pp512` | **428.43 ± 1.01** |
| llama-bench `pp16384` | **325.35 ± 1.59** |
| llama-bench `tg64` | **29.97 ± 0.03** |
| llama-server EN 34→64 | decode **30.09** |
| llama-server CS 45→64 | decode **30.06** |
| llama-server pp4205 | prefill **427.9** |
| tool call `get_time` | `finish=tool_calls` **PASS** |

Backend column **must** be `Vulkan`.

## 1. Runtime

Download the **v0.7.2** portable Vulkan tree from Nathanw’s releases. Point ICD at the **bundle**, not system Mesa (system Mesa here is `GFX1151` / `int dot: 0` — that is a 4× prefill loss on 27B).

```bash
NW="$MODELS/strix-halo-llamacpp-v0.7.2/vulkan"
export VK_ICD_FILENAMES="$NW/driver/radeon_icd.x86_64.json"
export LD_LIBRARY_PATH="$NW/bin:$NW/driver"
"$NW/bin/llama-bench" --list-devices
# expect: Vulkan0 Radeon 8060S (RADV STRIX_HALO)
```

## 2. Weights

```bash
# verify size against HF tree API, not ls -lh
stat -c%s "$MODELS/Qwen38-Flash-Next/AP-IQ4_XS/Qwen3.8-Flash-Next-AP-IQ4_XS.gguf"
# must be 90447294368
```

HF: `https://huggingface.co/agentionai/Qwen3.8-Flash-Next-AP-GGUF/resolve/main/AP-IQ4_XS/Qwen3.8-Flash-Next-AP-IQ4_XS.gguf`

Do not bench a truncated file. `ls -lh` said “85 G” on a 2.6 GiB-short PLE GGUF.

## 3. Bench

```bash
"$NW/bin/llama-bench" -m "$AP" -ngl 99 -ncmoe 0 -ub 256 -fa on \
  -dev Vulkan0 -p 512,16384 -n 64 -r 3 -o md
```

## 4. Serve (production Flash = 128k)

```bash
"$NW/bin/llama-server" -m "$AP" \
  --host 127.0.0.1 --port 18081 --alias qwen38-flash-next \
  --device Vulkan0 --gpu-layers 99 --flash-attn on \
  --ctx-size 131072 --ubatch-size 256 \
  --reasoning-effort medium --reasoning-budget 256 \
  --jinja --no-webui --parallel 1 \
  --temp 0.7 --top-p 0.8 --top-k 20
```

| `-c` | RAM used / avail (this 124 GiB box) | notes |
|---|---|---|
| 65536 | 99 / 25 GiB | Hermes minimum; decode still ~30 |
| **131072** | **103 / 21 GiB** | **production** |
| 262144 | 108 / 16 GiB | loads; too tight |

`--reasoning auto` is **HTTP 500** on this jinja (`low` / `medium` / `xhigh` only). `xhigh` is **not longer** than `medium` (same hard prompt, uncapped: ~32 s / ~2500–3100 thought chars). Client `none` skips thought (~0.25 s).

Nathanw **cannot** load Flash-Next MTP (`tensor 'output_hc_norm.weight' not found`).

**Never `llama-cli`:** default n_ctx 262k hangs; `-no-cnv` was ignored on this binary (19 GiB stdout).

## Same-day non-winners

| candidate | prefill | decode | verdict |
|---|---|---|---|
| CIRU HIP IU4 no-MTP | pp4205 **433.6** | **22.6** tg64 | prefill tie; decode slower; PLE needs ext4 `O_DIRECT` |
| cyjin-yl 27B Cyber IQ4_XS | pp512 334 | 13.3 | worse than Heretic-Ara MTP 18.9 |
| apepojken qwen4exp-spec-mtp | — | abort | `ggml-vulkan.cpp:7794` MUL_MAT_VEC on AP-IQ4. Reddit ~50 t/s was **UD-Q3_K_XL**, not IQ4 |
| julianmb/haloq38flash | — | 56 t/s MTP @ 8k; **19–27 @ 128k** | slower than 30 t/s here at the ctx we actually use |

CIRU MTP + PLE: `CIRUPLE1 supplied for a Qwen4Exp model without PLE metadata`. Do not combine.
