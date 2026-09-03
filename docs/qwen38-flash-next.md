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
| llama-server EN/CS | decode **30.09 / 30.06** (8k, 2026-08-30) | **128k 2026-09-01: EN 29.42 / CS 29.51** | wash |
| tool call `get_time` | `finish=tool_calls` **PASS** | **PASS** (128k) | — |

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

## Measured 2026-09-01 — Orca Uncensored Q4_K_M + MTP sidecar · Nathanw v0.7.3

**Hilbert `llama-server` `print_timing` / JSON `timings.*`. Not llama-bench. Not their Fedora/b10685 table.**

Stock HF 3 shards (111 GiB) + EasiiX `mtp-Qwen3.8-Flash-Next-Q8_0.gguf`. Nathanw v0.7.3 `df1671a03` b10654. Port `:18090`, 1 slot, `-c 65536`. Sidecar loaded. Telegram default unchanged. Pop!_OS unchanged.

Flags: `-ngl 999 -fa 1 -c 65536 -b 2048 -ub 2048 --cache-type-k q8_0 --cache-type-v q8_0 --load-mode mmap --tensor-read-lazy auto --no-host --no-repack --spec-type draft-mtp -md … --spec-draft-n-min 0 --spec-draft-n-max 7 --spec-draft-p-min 0.75 --reasoning off`

| workload | prompt_n | pp t/s | gen | decode t/s | draft acc |
|---|---:|---:|---:|---:|---:|
| EN unique code ×3 | 80 | 132.8 first | 512 | **58.3–58.7** | 95% |
| EN code + 2k filler | 2124 | 378.9 | 512 | 60.3 | 99% |
| Czech prose ×2 | 752 | 432.5 first | 256 | **30.4–30.7** | 70% |
| EN @ ~26k ctx | 26467 | 405.8 | 256 | 41.3 | 87% |

Czech ≈ AP-IQ4_XS 30 t/s (MTP mean draft 2.4). Code is the MTP win. 65k decode not measured. Community 49.6/43.6 remain **their** numbers.

## Measured 2026-09-02 — Unsloth MIX b10715 ROCm gfx1151 + Orca + shared MTP

**Same Orca Q4_K_M 3-shard weights.** Runtime `unslothai/llama.cpp` `b10715-mix-86bd2d3` `linux-x64-rocm-gfx1151`. Device `ROCm0` 8060S. `:18090`, `-c 8192`. Telegram default unchanged. Pop!_OS unchanged.

EasiiX self-contained Q8_0 sidecar **rejected** (`blk.48.nextn.hc_head_norm.weight` missing). Unsloth `MTP/mtp-Qwen3.8-Flash-Next-shared-Q8_0.gguf` **2,786,568,256 B** loaded and drafted.

Vendor Unsloth MTP guide (greedy, NVIDIA B200, `UD-Q4_K_XL`): 83.2 → 138.8 t/s (1.67×). **Not a Hilbert number.**

| workload | prompt_n | pp t/s | gen | decode t/s | draft acc | mean draft |
|---|---:|---:|---:|---:|---:|---:|
| Czech prose | 42 | 98.6 | 138 | **25.60** | 63.8% | 2.33 |
| EN unique code | 37 | 102.8 | 512 | **42.37** | 83.4% | 5.18 |

`llama-server print_timing`. `--spec-type draft-mtp --spec-draft-n-max 7`. ROCm0 has no TOP_K sampler op (warning). Decode **lost** vs Nathanw Vulkan + EasiiX (Czech 30.4 → 25.6; EN code 58 → 42). Keep Nathanw as the Orca path. Do not mix into the AP-IQ4 30 t/s table.

## Measured 2026-09-03 — llama.cpp PR #28136 `on-direct` (pread) vs mmap

**Hilbert `llama-server` JSON `timings.prompt_per_second`. Not llama-bench. Not DGX Spark.**

[PR #28136](https://github.com/ggml-org/llama.cpp/pull/28136) is **OPEN** (unmerged). Parallel `pread()` workers instead of mmap 4 KB page faults on the Flash-Next PLE/n-gram table. Nathanw v0.7.3 has `--tensor-read-lazy` (mmap), **not** `--lazy-mode on-direct`. Isolated HIP build of ggml-org + the PR, commit `c6a9e5c`, `gfx1151`.

Weights: same AP-IQ4_XS `Qwen3.8-Flash-Next-AP-IQ4_XS.gguf` · **90,447,294,368 B**. Port `:18090`, 1 slot, `-c 32768 --ubatch-size 256 --flash-attn on`. XOR `:18081`. Telegram default unchanged. Pop!_OS unchanged. `n_predict=1` — **decode not measured**. No `drop_caches`. Prompt 28,728 tokens (Czech padding, not fully unique PLE). Marker `PR28136_HILBERT_20260903_COLD_210P7`.

| `--lazy-mode` | tag | prompt_n | prompt_ms | pp t/s | vs mmap cold |
|---|---|---:|---:|---:|---|
| `on` (mmap) | cold | 28728 | 150871.583 | 190.41 | baseline |
| `on-direct` (pread) | cold | 28728 | 136328.921 | **210.73** | **+10.7%** |
| `on` (mmap) | warm | 28728 | 135975.715 | 211.27 | +11.0% vs own cold |
| `on-direct` (pread) | warm | 28728 | 136621.784 | 210.27 | −0.5% vs mmap warm |

Cold prefill moved; warm is a wash (page cache already hot). DGX Spark 2–3× (~300 → 750–800 t/s) did **not** reproduce on this 124 GiB unified box. Community Strix Halo +20–32% cold prefill is the right band; this run is the low end.

**Not production.** Do not wire into `zapni flash`. Do not mix into the AP-IQ4 30 t/s decode table.

