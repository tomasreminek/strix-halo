# Qwen3.8 27B on Strix Halo

Use this when you need **cache-reuse / context-shift** (full agent). Flash-Next is faster
decode (~30 t/s) but qwen4exp disables KV shifting.

Measured 2026-08-28 … 2026-08-30. gfx1151, 124 GiB, one GPU job.

## What to run

| Role | Weights | Decode (Czech prose) | Notes |
|---|---|---|---|
| **Main agent** | julianmb ROCmFP4 FAST (ggml type 101) | **14.2 t/s** no draft · **20.2 t/s** MTP n-max=2 (73% acc) | not portable to upstream llama.cpp |
| **Code worker** | same + DFlash2 | Czech **10.3** · code **57.0** | DFlash is workload-split |
| **Uncensored** | Heretic-Ara | **14.2** no draft · **18.9** MTP (69.7% acc) | keep this; cyjin IQ4_XS is **13.3** |

Live later check on main: **22.1 t/s / 82.5%** acceptance with n-max=2.

## Fork × quant is not portable

ROCmFP4-FAST uses ggml **type 101**. Upstream llama.cpp:

```
gguf_init_from_reader: tensor 'output.weight' has invalid ggml type 101
```

A/B needs **three** arms (build vs quant). On Nathanw v0.7.1 + stock UD-IQ4_XS vs our Laurent fork:

| build + model | pp512 | pp@16k | tg64 |
|---|---:|---:|---:|
| Laurent + ROCmFP4-FAST (production) | 60.9 | 55.9 | 14.13 |
| Laurent + Unsloth UD-IQ4_XS | 62.1 | 56.9 | 14.24 |
| **Nathanw v0.7.1 + UD-IQ4_XS** | **270.2** | **230.6** | 14.37 |

Prefill **4.4×** (bundled Mesa `int dot: 1` / `fp16: dot2`). **Decode did not move (~14 t/s).**
The custom FAST quant bought nothing vs stock IQ4_XS on our own build.

Weights:

- Production FAST: [`julianmb/Qwen-3.8-27B-ROCmFP4-FAST-GGUF`](https://huggingface.co/julianmb/Qwen-3.8-27B-ROCmFP4-FAST-GGUF)
- Uncensored: [`cygnal/Qwen3.8-27B-heretic-ara-Q4_K_M-MTP-GGUF`](https://huggingface.co/cygnal/Qwen3.8-27B-heretic-ara-Q4_K_M-MTP-GGUF)
- MTP sidecar: `mtp-Qwen3.8-27B-Q4_0.gguf` (1.68 GB) — drafts the 27B FAST target
- cyjin (measured, **not** the uncensored worker): [`cyjin-yl/Qwen3.8-27B-Uncensored-Cyber-agentic-imatrix-GGUF`](https://huggingface.co/cyjin-yl/Qwen3.8-27B-Uncensored-Cyber-agentic-imatrix-GGUF) plus-mtp `16,517,175,520` B

## MTP: tune acceptance, not vendor n-max

AMD documents MTP=4 for Ryzen AI Max+. On **Czech prose** that was the wrong number.

| config | Czech prose | code |
|---|---|---|
| no draft | ~14.1 t/s | ~14.1 t/s |
| `--spec-draft-n-max 4` (AMD blog) | 17.5 t/s · **25% acc** | 29.5 t/s · 62% acc |
| **`--spec-draft-n-max 2 --spec-draft-p-min 0.6`** | **20.2 t/s · 73% acc** | 28.4 t/s · 92% acc |

Rejected draft tokens are wasted verify work. Optimise **acceptance**, on the **primary** language, not on code.

## Agent launcher (not the bench launcher)

`--temp 0 --seed 42` with no repetition penalty **loops identical tool calls** 50–150×.
That is a sampler fixed point, not a harness bug.

```text
--temp 0.7 --top-p 0.8 --top-k 20 --min-p 0.0
--repeat-penalty 1.05 --repeat-last-n 256
--presence-penalty 1.0
--dry-multiplier 0.8 --dry-base 1.75 --dry-allowed-length 4
```

Agent flags that actually matter on 27B (Flash-Next cannot do these):

```text
--ctx-size 65536
--cache-reuse 256
--slot-save-path <dir>
--context-shift
--parallel 1
--spec-draft-n-max 2 --spec-draft-p-min 0.6
```

Warm turn: 31.5K-token repeated prefix in **1.6–1.9 s** wall with cache-reuse.
Clear `--slot-save-path` when switching models (stale KV = another loop source).

## Structured-output 55.6 t/s is not chat

Laurent Vulkan + julianmb FAST + DFlash2 `n-max=7`, temp 0, JSON count 0–250:
**55.6 t/s mean**, but completion stopped at ~123/250. Prose on that profile was ~21.7 t/s.
Do not quote 55.6 as a general Strix Halo number.

Evidence hashes (that profile only):

- target FAST SHA-256 `fb89c78d2be91cdb68eaaaa45b1270710bf34aa721dc1f0b9e3aa7b98d2e1da9`
- DFlash2 Q4_K_M SHA-256 `18a380efc9b7ed8d88677fc895f5c11ae170653434ee378f7348f715c14d0594`
- runtime LaurentZuijdwijk/llama.cpp `16f0799a668757f17e3e6a4801ffc8acba5019f2`

## Failed 27B lines

| candidate | result |
|---|---|
| cafonez ROCmI4 MTP GGUF | parser rejects tensor type 108 |
| Kairic Edge IU4 | 31.26 t/s single MTP run; dropped vs FAST |
| cyjin IQ4_XS | 13.3 t/s decode — keep Ara |
