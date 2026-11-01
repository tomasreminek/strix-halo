# Gufo + DeepSeek V4.1 Flash 1017 IQ1_M on one Strix Halo · 2026-11-01

A **671B-class MoE running at 24 tok/s decode and 1.2–1.3k tok/s prefill on a single Ryzen AI MAX+ 395**, from 120.72 GB of IQ1_M backbone plus a 150.21 GiB Engram borrowed from a different quantization. Context depth is nearly free: 32k → 128k costs 10 % prefill and 3 % decode. Two request slots (`-j 2`) raise aggregate output by **+36 %**, and prompt lookup raises decode **3.3×** on copy/edit work.

This document is the **replication recipe**, not just a result table. Every number here came from a run on the box described in [00 hardware](00-hardware.md); the frozen logs are in [records/benchmarks/gufo-iq1m-20261101](../records/benchmarks/gufo-iq1m-20261101/) and the scripts are in [recipes/deepseek-v41](../recipes/deepseek-v41/).

**Status: research runtime, not production.** Quality gate passed 2 of 3 fixtures — the Czech answer to a geography question came back as "Ne" instead of "Paris". **That failure is a harness artefact, not a weight problem:** the gate ran with `--think off`, and V4.1 Flash is a reasoning model. Re-run through the API the same prompt answers `Paříž` with thinking on and `Ne` with `reasoning_effort: none`. Re-run of the fixed gate (thinking on) on 2026-11-01 11:17 gives **`VYSLEDEK: PASS (3/3)` in 70 s**. See §5. Treat it as a fast worker under supervision, not as an authority. The two-slot server was left running as a test instance on port `:18092`; nothing was switched onto the production port.

## Why this exists

Earlier DeepSeek V4.1 work on this box ([single host](deepseek-v41-single-strix-halo.md), [overnight](deepseek-v41-night-20260917.md), [second pass](deepseek-v41-speed2-20260917.md), [Project Maya](maya-v1126-20261024.md)) topped out at 7.12 tok/s of HTTP completion through the `ds4` Q2 streaming path. This run uses a **different runtime** (the `franzmoca/gufo` fork, branch `feat/ds41`) and a **different quantization** (ISTA IQ1_M). **The numbers are not comparable** — different decoder, different weights, different measurement method. Do not put these in the same table as the `ds4` rows.

## What was actually run

| Component | Version / value | Where |
|---|---|---|
| Runtime | `franzmoca/gufo`, branch `feat/ds41`, commit `7f8d6430` + local patch | `~/Projekty/gufo-ds41` |
| Binary | `build/gufo`, 354,018,752 B, 322/322 targets | same |
| Toolchain | `strata-rocm-7.14.1-gfx1151`, clang 23 | `~/toolchains/` |
| HIP arch | `gfx1151` | — |
| Backbone | ISTA `DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M`, 5 shards, **120,721,194,336 B** | `/mnt/c/AI-Models/.../ISTA-IQ1M/` |
| Engram | Maya-S `blk.1` + `blk.14` `engram_embd`, **Q6_K, 210 B/row, 150.21 GiB** | `/mnt/c/AI-Models/.../Maya-S/` |
| Host | AMD Ryzen AI MAX+ 395, Radeon 8060S, 124.9 GiB unified LPDDR5X, `amdgpu.gttsize=131072` (128 GiB GTT) | — |

## 1. Build

Dependencies (Debian/Ubuntu names): `libpng-dev libjpeg-dev libwebp-dev libssl-dev openssl libstdc++-14-dev`. The fork's CMake looks for a ROCm root, and the Strix Halo toolchain is not installed system-wide, so give it one:

```bash
TC=$HOME/toolchains/strata-rocm-7.14.1-gfx1151
sudo ln -sfn "$TC" /opt/rocm          # the HIP compiler is looked up as /opt/rocm/bin/clang

cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DENGINE_ENABLE_HIP=ON \
  -DCMAKE_HIP_ARCHITECTURES=gfx1151 \
  -DCMAKE_HIP_COMPILER=/opt/rocm/bin/clang \
  -DCMAKE_HIP_FLAGS="--rocm-path=$TC" \
  -DCMAKE_PREFIX_PATH="$TC/install"
ninja -C build -j32
```

Two failure modes we hit, both environmental rather than model-related:

- `Failed to find ROCm root directory` → the `--rocm-path` plus `/opt/rocm` symlink above.
- `find_package(PNG)` failing → the `-dev` packages above.

The build must produce **322/322** targets. A partial build silently loses the grouped expert GEMV kernels and every expert projection then falls back to a slow path.

## 2. Weights — ISTA IQ1_M, five shards

Source: `ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF`, files `DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-0000N-of-00006.gguf`.

| Shard | Bytes | SHA256 |
|---|---|---|
| 00001 | 5,780,704 | `3e8ddd11441edd4bc19bacaef5dbe38818af2cbdf0820fb70f1d2d851fcc192a` |
| 00002 | 39,340,012,896 | `be4ceb1caf1bed28e886860cf6a52adc8f5ca9eb0d2098ade39bb4179d48b323` |
| 00003 | 38,698,805,888 | `758c66ba65236e8ce0820c21a7b6f9b2947681df8cc509f672a77722e8191b9a` |
| 00004 | 39,707,055,008 | `04a5bea2b38eb576f49efc19c0a677768d6e2a8ea5772d72fb6cb79e1733a212` |
| 00005 | 2,969,539,840 | `7c8dbee99890f05dbc420eba6f44393f5228d06248fe61e1ae8ed002449c7549` |
| **total** | **120,721,194,336** | |

**Shard 00006 of the ISTA repo is the Engram table and is deliberately not downloaded** — see §3. It is 110,595,290,816 B of IQ4_NL that the drop-in makes unnecessary.

Use [`fetch-verify-iq1m.sh`](../recipes/deepseek-v41/fetch-verify-iq1m.sh): it pins the size and SHA256 of each shard, downloads with up to 3 attempts, and refuses to continue on a mismatch.

> **Do not resume a shard with `curl -C -`.** We corrupted shard 2 this way: the file ended up shifted by **+24,735,744 bytes** from offset 3,777,633,632, which surfaced much later as a `NaN` in layer 1 during the `q⊙k` verification. Recovering it meant `truncate -s 2099924706` followed by a clean re-download. The script truncates before retrying for exactly this reason. If a run dies mid-shard, delete the partial file and start that shard again.

## 3. The Engram drop-in — how 110.6 GB were saved

DeepSeek V4.1 Flash carries two **Engram** tables (`blk.1.engram_embd`, `blk.14.engram_embd`) — a sparse 768,022,850-row hash-indexed embedding, **210 bytes per row**. Upstream ISTA ships them as a separate ~110.6 GB IQ4_NL shard.

The Maya-S quantization of the *same model* already contained those two tables as **Q6_K** in its shards 5 and 6 (`-00005-of-00006`, `-00006-of-00006`). Engram rows are global (`0…768M`), not per-shard, so the tables are interchangeable with the backbone as long as the reader accepts a different type and a different row layout.

We therefore run **ISTA IQ1_M backbone (5 shards) + Maya-S Q6_K Engram (2 tables)**. Layout:

```bash
mkdir -p models/ista-iq1m && cd models/ista-iq1m
R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF
for n in 1 2 3 4 5; do
  ln -sf "$R/ISTA-IQ1M/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-0000$n-of-00006.gguf" .
done
# shard 06 in this directory IS the Maya-S blk.1 table
ln -sf "$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00005-of-00006.gguf" \
       DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf
```

and point the runtime at both tables explicitly:

```bash
export DS41_ENGRAM_SHARDS="models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf:\
$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00006-of-00006.gguf"
```

This **requires the patch** [`gufo-ds41-engram-dropin.patch`](../recipes/deepseek-v41/gufo-ds41-engram-dropin.patch) (4 files, +327/−82):

| File | Change |
|---|---|
| `src/core/gguf_reader.cpp` | accept `blk.<N>.engram_embd.weight` as a shared Engram tensor (Maya-S declares 1044 tensors, ISTA 1043) |
| `src/models/deepseek_v41_flash/runtime/model_data_internal.h` | per-table Engram descriptors |
| `.../runtime/model_data.cpp` | `engram_place()`, `engram_row_type_ok()`, two `engram_open()` paths, `DS41_ENGRAM_SHARDS`, Maya-S metadata fallback (`hash_layer_count`→0, `ple.*` from `engram.*`, `engram_head_vocab[i] = primes[i]`) |
| `.../runtime/v41_decode.cpp` | multi-table `engram_read()` |

With the patch the load completes in **6.46 s**: **112.00 GiB backbone + 150.21 GiB Engram**, 210-byte rows. The decoder already supported Q6_K dequantization (`dequant_row()`); only the loader refused it.

**Caveat, stated plainly:** the Q6_K Engram path is not what the upstream authors test. It loads, it produces coherent output on two of three fixtures, and it is bit-exact against the reference on the `q⊙k` gate — but it is a local modification. If you have the disk, the stock IQ4_NL Engram shard is the untested-by-us, supported path.

## 4. The cgroup trap — wrap every run

`hermes-gateway.service` runs with `MemoryMax=25769803776` (24 GiB). A gufo process started from a Hermes shell **inherits that limit**, and the result looks like a broken model rather than a broken launch:

- visible memory 3.83 GiB, expert cache 0.00 GiB
- decode **5.76 tok/s** instead of ~24

Every run in this document was executed as:

```bash
systemd-run --user --scope --quiet --collect -p MemoryMax=infinity \
  --unit=gufo-<tag>-$$-$RANDOM ./build/gufo ...
```

If you measure from a plain shell, skip the wrapper. If you measure from anything cgroup-managed, **do not skip it** — you will report the cgroup, not the model.

## 5. Quality gate — 2 of 3 with thinking off, 3 of 3 with it on

**Result of the corrected gate, 2026-11-01 11:17: `QUALITY GATE: 0 selhani ze 3` / `VYSLEDEK: PASS (3/3)`, 70 s wall.**
Raw output kept at [`records/benchmarks/gufo-iq1m-20261101/quality-thinking-on-20261101.txt`](../records/benchmarks/gufo-iq1m-20261101/quality-thinking-on-20261101.txt).
The original `--think off` run is preserved as `quality.txt`; do not read it as a quantization verdict.

Greedy, seed 42, three fixtures ([`quality.txt`](../records/benchmarks/gufo-iq1m-20261101/quality.txt)):

| Fixture | Expect | Result |
|---|---|---|
| arithmetic | `391` | **PASS** |
| code | `s[::-1]` / `reversed` | **PASS** |
| Czech geography | `Paříž` / `Paris` | **FAIL with `--think off`** — answered "Ne" · **PASS with thinking on** — answered `Paříž` |

IQ1_M is a 1.6-bit-class quantization; this is the price. The runtime is usable for generation, editing and tool-style work under supervision, and is **not** trustworthy as a factual authority without a check.

### Thinking on versus off — same decode speed, different latency

The QA gate in the previous section is only the visible part of a larger question: what does
reasoning cost in throughput? Measured 2026-11-01 against the running server on `:18092`,
streaming, `temperature: 0`, token counts from the SSE deltas, three tasks in both modes.
Raw numbers: [`records/benchmarks/gufo-iq1m-20261101/reasoning-on-vs-off.csv`](../records/benchmarks/gufo-iq1m-20261101/reasoning-on-vs-off.csv).

| Task | Mode | Reasoning tok | Answer tok | Seconds | tok/s | First answer token |
|---|---|---|---|---|---|---|
| France capital | thinking on | 43 | 3 | 3.4 | 13.66 | 3.2 s |
| France capital | thinking off | 0 | 3 | 0.4 | 7.53 | 0.3 s |
| Train Prague–Brno | thinking on | 49 | 68 | 6.3 | 18.68 | 3.4 s |
| Train Prague–Brno | thinking off | 0 | 95 | 4.2 | 22.37 | 0.3 s |
| Longest common subsequence | thinking on | 442 | 247 | 28.9 | 23.82 | 19.2 s |
| Longest common subsequence | thinking off | 0 | 150 | 6.6 | 22.68 | 0.4 s |

**Decode speed does not change.** Thinking does not generate slower — it generates *more tokens*,
through the same autoregressive loop. Means: 18.72 tok/s with thinking, 17.53 tok/s without; the
spread is noise, and the long generation confirms it (23.82 versus 22.68, both at the ~24 tok/s
ceiling that the serving bench reports).

The short generations read low for a different reason: prefill and first-token latency are inside
the divisor. Three answer tokens in 0.4 s is 7.53 tok/s as arithmetic, not as a decode rate.

**What actually costs is time to first answer token.** The model must finish the whole reasoning
block before it emits the first word the user sees:

- trivial question — 3.2 s instead of 0.3 s
- word problem — 3.4 s instead of 0.3 s
- code — **19.2 s instead of 0.4 s**, total wall 28.9 s versus 6.6 s (4.4×)

**Reasoning length is self-selected.** 43 tokens for a one-word fact, 49 for an arithmetic word
problem, 442 for an algorithmic problem. Nothing sets that budget; the model decides how hard the
task is. Also worth noting: with thinking on the word-problem *answer* got shorter (68 versus 95
tokens) because the working was done in the reasoning block instead of being written out.

**Tool calling works on this server.** Verified against `:18092`: a `tools` request returned
`finish_reason: "tool_calls"` with `get_weather({"city": "Praha"})` in 39 tokens at 22.18 tok/s.
This is what makes the two slots usable as an agent backend rather than a chat toy — the same
endpoint can serve a tool-calling harness.

## 6. Throughput — the matrix

`gufo bench`, `-p 2048 -n 128`, streamed experts from SSD, own systemd scope. `stream_warm` is the first run after the page cache is warm; `stream` is a cold-cache repeat.

| Config | Depth | Prefill tok/s | Decode tok/s |
|---|---|---|---|
| smoke (`-p 64 -n 8`) | 0 | 79.85 | *invalid* |
| **stream warm** | 0 | **1027.73** | **23.27** |
| stream | 0 | 719.64 | 17.50 |
| stream | 8,192 | 1289.26 | 24.12 |
| stream | 32,768 | 531.11 | 19.53 | 
| stream | 131,072 | 1074.96 | 23.03 |
| `--expert-cache-bytes` 64 GiB | 0 | 782.25 | 18.99 |
| `--expert-cache-bytes` 32 GiB | 0 | 561.16 | 12.38 |
| `--expert-cache-bytes` 16 GiB | 0 | 478.60 | 9.77 |
| resident (no streaming) | 0 | **FAIL** | **FAIL** |

Reading notes, because three rows are easy to misread:

- The 32,768 row (**531 / 19.53**) is **noise, not a trend** — both 8k and 128k came out higher. It was replaced by the repeated sweep in §7 and must not be quoted.
- The smoke row's decode is **invalid**: `-n 8` mostly fills KV cache and does not measure steady-state decoding. Its purpose is only "does it load and answer".
- `--expert-cache-bytes` takes **bytes**, not `64G`. Passing `64G` fails with `Invalid integer`. Use `68719476736` / `34359738368` / `17179869184`.
- A small expert cache is *worse than none*: 16 GiB gives 9.77 tok/s against 23.27 for pure streaming, because the cache thrashes instead of letting the OS page cache do the work.

## 7. Context depth is nearly free

`-p 2048 -n 128 -d <depth>`, two repetitions each, [`depth-sweep.csv`](../records/benchmarks/gufo-iq1m-20261101/depth-sweep.csv):

| Depth | Prefill tok/s | Decode tok/s |
|---|---|---|
| 32,768 | 1264.18 / 1267.77 | 23.53 / 23.55 |
| 65,536 | 1197.86 / 1215.96 | 23.34 / 23.39 |
| 131,072 | 1141.51 / 1127.03 | 22.85 / 22.75 |

Reproducibility ±2 %. Going from 32k to a full 128k costs **10 % prefill and 3 % decode** — there is no reason to economise on context with this runtime.

Practical prefill wall time: **≈1.6 s for 2k tokens, ≈8 s for 10k, ≈115 s for a full 128k prompt.**

## 8. Prompt lookup — the biggest free lever (3.3×)

For V4.1 Flash the fork hardcodes `kPromptLookup = true` in `src/cli/prompt/prompt.cpp` and `src/cli/serve/inference_backend.cpp`. On copy/edit work — the normal shape of iterative coding — the decoder copies spans straight out of the prompt instead of sampling them.

Measured with an **n-delta method** that cancels load time (6.5 s) and prefill: time `n=192` minus time `n=64`, divided by 128.

| Arm | t(64) | t(192) | Δ | Decode |
|---|---|---|---|---|
| novel generation | 24.05 s | 30.40 s | 6.35 s | **20.16 tok/s** |
| copy / edit | 23.49 s | 25.42 s | 1.93 s | **66.32 tok/s** |

**3.3×**, with the counters confirming the mechanism: `lookup_cycles=9 lookup_copied=109 lookup_accepted=102 full_block_rate=0.889` on the copy arm, versus all zeros on the novel arm. Disk traffic drops **26.69 → 10.71 MiB/token** and host wait drops **27.97 → 8.16 ms/token**. An earlier single-prompt probe saw 102 of 118 tokens (86 %) taken from the prompt.

**`gufo bench` does not use prompt lookup at all** (it only offers `--speculative dspark|off`). Every number in §6 and §7 is therefore the **pessimistic, novel-generation** case. Report both figures; quoting only the bench number understates real interactive speed by more than 3×.

## 9. Two slots — `-j` is batching, not a queue

`gufo serve` has no `--parallel`/`--slots`. The relevant flag is **`-j/--sessions`** ("preallocated GPU request sessions", default 1), and `src/models/deepseek_v41_flash/engine.cpp:121` states DeepSeek batch decode **requires two to eight sessions**. `SERVER.md` confirms the scheduler serializes model execution and that dense and expert projections share weight reads across a batch.

```bash
# recipes/deepseek-v41/serve-2slot.sh
systemd-run --user --scope --quiet --collect -p MemoryMax=infinity \
  --unit=gufo-serve-test \
  ./build/gufo serve llm --stream-experts -j 2 -c 65536 \
    -i 127.0.0.1 -p 18092 \
    --model models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf
```

Ready in **21 s**, RSS **94 GB**, expert cache **88.83 GiB**, ~8 GB RAM left. Benchmarked with `tools/serving/gufo-serving-bench.py --prompt-repeat 4 --max-tokens 128 --warmup 1 --repetitions 2`:

| Concurrency | Decode tok/s | ITL p50 | Prefill tok/s | Output aggregate |
|---|---|---|---|---|
| 1 | **24.10** | 41.84 ms | 871.11 | **19.20 tok/s** |
| 2 | 18.88 /request | 53.79 ms | 799.02 | **26.16 tok/s** |

**Aggregate output +36 %** (19.20 → 26.16) at a cost of −22 % per stream. The log shows `plan=batched-w2`: the expert weights are read **once for both requests**. With disk-streamed experts, batching is a genuine win, not a latency trade.

That is the shape we wanted: **one slot for chat, one for a coding worker**. Interactive latency stays well inside human reading speed while the worker keeps the second slot busy.

**Prefix cache is the second lever.** A repeat request sharing the system prompt returns `cached_tokens=320, prefill_tokens=0, ttft_ms=1.3` against `ttft_ms=946` cold. Long stable system prompts are effectively free.

Harness sharp edges, both of which cost us a run: `gufo-serving-bench.py` defaults to `result/bin/gufo` (pass `--gufo ./build/gufo`), and `gufo diagnose` exits 127 without `LD_LIBRARY_PATH` pointing at the ROCm libraries.

## 10. What did not work

Recorded so nobody repeats it:

- **`--prefill-batch 4096`** — pp8192 moved 1276 → 1293 tok/s (**+1.3 %, i.e. noise**). No change made.
- **`--draft-tokens 15`** — rejected; the flag requires `--draft-policy dflash2`, and that policy is not usable here. The lookup window cannot be widened from the CLI.
- **DSpark drafter** — `drafter-src/` holds `dspark.json` + `dspark.bin` (16 GB) but the engine expects GGUF and will not load the `.bin`. Speculative decoding with DSpark is unavailable.
- **Resident (no streaming)** — needs **114.00 GiB**, box offers **102.21 GiB** (111.2 GiB `MemAvailable` minus 9.13 GiB `CmaFree`). `ds41_expert_available_memory()` reads `/proc/meminfo` directly and has no override; the only route is `kho=off` in GRUB plus a reboot, worth roughly +14 % prefill / +6 % decode. **Not worth it.** The authors' quoted 1228/24.5 tok/s is a resident configuration this machine cannot reach.
- **Maya-S as the backbone** — closed. Layers 0–3 are `IQ2_S`/`IQ3_S` and `gufo` has no table-indexed kernel for `IQ3_S` (type 21); `v41_decode.cpp:1295` fails with "no table-indexed kernel for this shape". Only its two Engram tables are usable here.
- **AtomicChat uncensored IQ1_M** — *not* a drop-in: 4 shards vs 6, 81 keys vs 77, `engram_gate` (F32) becomes `engram_q`+`engram_k` (BF16), `engram_kv`→`engram_wkv`, 40× `exp_probs_b_vl.bias` missing, Engram constants as I64. The `q⊙k == engram_gate` equivalence is bit-exact (verified, layer 14), so a port is real work rather than impossible — roughly a day. Source: `AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF` on Hugging Face (MIT); the vendored DGX Spark copy that used to hold these notes was removed on 2026-11-01.

## 11. Disk budget

| Item | Size | State |
|---|---|---|
| ISTA IQ1_M shards 1–5 | 120.72 GB | kept, SHA256-verified |
| Maya-S Engram shards 5+6 (Q6_K) | 150.21 GiB | kept — required by the drop-in |
| ISTA IQ4_NL Engram (shard 06) | 110.60 GB | **never downloaded** |
| Maya-S backbone shards 1–4 | 166 GB | **deleted 2026-11-01** ([manifest](../records/benchmarks/gufo-iq1m-20261101/maya_s_removal_manifest.txt)) |
| DSpark drafter sources | 16 GB | present, unusable |
| **`/mnt/c` free after cleanup** | **240 GB** | was 74 GB |

The Maya-S backbone was removed only after confirming no running process held an open handle to any `.gguf` and that the Project Maya configuration points at its native `maya-ds4` format instead.

## Reproduce, in order

1. Install the deps from §1 and symlink `/opt/rocm`; build to 322/322.
2. Run `recipes/deepseek-v41/fetch-verify-iq1m.sh` — five shards, SHA256 pinned.
3. Build `models/ista-iq1m/` with the six symlinks from §3 (five ISTA + Maya-S shard 5 as `-00006`).
4. Apply `recipes/deepseek-v41/gufo-ds41-engram-dropin.patch` and rebuild.
5. Export `DS41_ENGRAM_SHARDS` to the two Maya-S Engram tables.
6. Wrap everything in `systemd-run --user --scope -p MemoryMax=infinity`.
7. `run-gufo-iq1m.sh` for a smoke run: expect load ≈6.5 s, 112.00 GiB backbone, 150.21 GiB Engram.
8. `quality-gate.sh` — expect 2/3.
9. `depth-sweep.sh` for the authoritative depth table; `speed-delta.sh` for the prompt-lookup delta.
10. `serve-2slot.sh` for the two-slot server, then `tools/serving/gufo-serving-bench.py --concurrency 1` and `2`.

## Evidence

- Frozen results, CSVs and raw bench logs: [records/benchmarks/gufo-iq1m-20261101](../records/benchmarks/gufo-iq1m-20261101/)
- Patch and scripts: [recipes/deepseek-v41](../recipes/deepseek-v41/)
- Interpretation and cross-model comparison: [model comparison](model-comparison.md) · [test index](llm-test-index.md)
