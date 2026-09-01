# Qwen3.8-Flash-Next on Strix Halo

**Current runtime 2026-09-01:** Nathanw **v0.7.3** + AP-IQ4_XS.

Not a full-skill Hermes daily driver: qwen4exp **disables** `--cache-reuse` and `--context-shift`
even when you pass them. 27B is still the agent path with persistent KV.

Exclusive ~84–103 GiB. Stop 27B, GLM, and Comfy first. Do **not** change the host OS to copy a Fedora recipe.

## Winner numbers (same weights, two runtimes)

Weights: [`agentionai/Qwen3.8-Flash-Next-AP-GGUF`](https://huggingface.co/agentionai/Qwen3.8-Flash-Next-AP-GGUF)
`AP-IQ4_XS/Qwen3.8-Flash-Next-AP-IQ4_XS.gguf` · **90,447,294,368 B** (84.23 GiB) · `qwen4exp A3B IQ4_NL - 4.5 bpw`.

Device (bundle ICD): `RADV STRIX_HALO | fp16: dot2 | int dot: 1 | fp4: 0`. Backend column **must** be `Vulkan`.

| test | v0.7.2 (2026-08-30) | v0.7.3 (2026-09-01) | delta |
|---|---:|---:|---|
| llama-bench `pp512` d0 | 428.43 ± 1.01 | 417.77 ± 0.83 | −2.5% (wash) |
| llama-bench `pp16384` d0 | 325.35 ± 1.59 | **373.13 ± 1.01** | **+14.7%** |
| llama-bench `tg64` d0 | 29.97 ± 0.03 | **30.09 ± 0.04** | wash |
| llama-bench `tg64 @ d16384` | — | 24.54 ± 0.09 | new |
| llama-server EN/CS 64 tok | decode **30.09 / 30.06** | not re-run | — |
| tool call `get_time` | `finish=tool_calls` **PASS** | not re-run | — |

v0.7.3 identity: portable Vulkan, llama.cpp **`df1671a03` (b10654)**. Author claim on a 64 GB box (`-ncmoe 8`, UD-Q3_K_XL) was +20% gen at 32k depth / +30% pp at 16k depth / flat at depth 0. On this 124 GiB box, full GPU (`-ncmoe 0`), AP-IQ4_XS: **decode at empty context did not move; long-prompt prefill did.**

v0.7.3 `llama-server --help` lists `--spec-type draft-mtp`. **Not measured** on AP-IQ4_XS (no grafted MTP head).

## 1. Runtime

```bash
NW="$MODELS/strix-halo-llamacpp-v0.7.3/vulkan"
"$NW/llama-bench" --list-devices
# expect: Vulkan0 Radeon 8060S (RADV STRIX_HALO)
# _run wrapper sets the bundle ICD
```

## 2. Weights

```bash
stat -c%s "$MODELS/Qwen38-Flash-Next-AP/AP-IQ4_XS/Qwen3.8-Flash-Next-AP-IQ4_XS.gguf"
# must be 90447294368
```

## 3. Bench

```bash
"$NW/llama-bench" -m "$AP" -ngl 99 -ncmoe 0 -ub 256 -fa on \
  -dev Vulkan0 -p 512,16384 -n 64 -d 0,16384 -r 3 -o md
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

`--reasoning auto` is **HTTP 500** on this jinja (`low` / `medium` / `xhigh` only).

**Never `llama-cli`:** default n_ctx 262k hangs; `-no-cnv` was ignored on Nathanw (19 GiB stdout).

## Same-day non-winners (2026-08-30)

| candidate | prefill | decode | verdict |
|---|---|---|---|
| CIRU HIP IU4 no-MTP | pp4205 **433.6** | **22.6** tg64 | prefill tie; decode slower |
| cyjin-yl 27B Cyber IQ4_XS | pp512 334 | 13.3 | worse than Heretic-Ara MTP 18.9 |
| apepojken qwen4exp-spec-mtp | — | abort | IQ4 MUL_MAT_VEC. Reddit ~50 t/s was **UD-Q3_K_XL** |
| julianmb/haloq38flash | — | 56 t/s MTP @ 8k; **19–27 @ 128k** | slower than 30 t/s here at 128k |

## Queued (not measured) — OrcaRouter uncensored Q4_K_M + MTP

Community claim on **same silicon**, different OS/runtime. **Hypothesis, not a Hilbert result.**

- Weights: `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF` **Q4_K_M** (HF tree: **3 shards**, 119,150,722,944 B ≈ 111 GiB). Their write-up is **113.55 GiB / 4 shards** after grafting a Q8_0 MTP head (PR 27836 converter, source rev `fdf5fe3`). Stock HF **does not** ship that 4th shard.
- Runtime they used: `myhacsint/llama.cpp` `production/strix-halo-qwen4exp-b10669` (b10669 / `3287a6e9d`), Fedora 44, Mesa 26.1.7. **Do not change Pop!_OS.**
- Claimed: short ctx pp512 485 / MTP decode **52.2 t/s code** (91% accept); 65k → 349 pp / **36.3** decode.
- That 52 t/s is **code + MTP + Q4_K_M**, not our AP-IQ4_XS 30 t/s empty-context tg64.
