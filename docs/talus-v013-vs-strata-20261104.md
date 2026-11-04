# Talus v0.1.3 vs Strata 0.1.56 · Qwen3.8-Flash-Next UD-IQ4_XS · 2026-11-04

Marker: `TALUS_013_VS_STRATA_20261104`.

Controlled A/B on the same box (Hilbert, Radeon 8060S gfx1151), **same weights, same pack, same quantization, same context, same client**. Both engines were measured with one script, in sequence, with nothing else running on the GPU.

## Arms

| | Strata | Talus |
|---|---|---|
| engine | `strata 0.1.56` (component `engine/0.1.56-linux-x86_64-hip-halo`) | `talus v0.1.3` (release tarball `talus-v0.1.3-linux-x86_64-gfx1151`) |
| weights | `Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf` (Unsloth UD IQ4_XS, 88 GB, 3 shards) | identical file |
| pack | `~/Projekty/Strata-data/packs/unsloth-ud-iq4_xs` | identical pack |
| quantization / KV | UD-IQ4_XS experts · int8 KV · `--kv-resident 32768` | identical |
| context | 131072 | 131072 |
| slots | `--batch 2` | `--batch 2` |
| expert cache | auto (resolved 24576 slots, 55.4 GiB) | 24576 slots, 55.4 GiB, profile `data/expert-profile.bin` |
| speculative | `--spec 4 --spec-min-p 0.5`, no MTP head available | `--spec 4 --spec-min-p 0.5`, no MTP head |
| prefill | `auto` | `auto` |
| ROCm | Strata's bundled HIP component | TheRock SDK `10.2.0a20261014` (pip wheel, `rocm-sdk` symlink) |

## Method

`bench_v2.py` (in this repo's `records/`), one methodology for both engines:

1. **Cold prefill.** A fresh random salt prefix is prepended to a corpus slice, so no prefix cache can satisfy the request, then `max_tokens=1`. `pp_tps = usage.prompt_tokens / wall_seconds`. The character count is calibrated per depth against `usage.prompt_tokens` to land within 3 % of the target depth.
2. **Decode.** The *same* prompt is sent again (prompt cache now warm) with `max_tokens=256`, streamed with `include_usage`. `tg_tps = completion_tokens / (t_last_delta − t_first_delta)`.
3. `temperature=0`, 128-output-token requests excluded, one sample per cell (this is a screening A/B, not a statistical campaign).

The first attempt at this measurement produced nonsense (137 000 tok/s "prefill") because the calibration probes had already cached the prompt — that is why the cold cell uses a **separate fresh salt**. Anyone reproducing this must keep that detail.

## Measured

| depth (tokens) | Strata prefill | Talus prefill | prefill gain | Strata decode | Talus decode |
|---|---:|---:|---:|---:|---:|
| ~2 000 | 564 tok/s | **1 049 tok/s** | **1.86×** | 32.2 | **37.3** |
| ~8 000 | 781 tok/s | **1 372 tok/s** | **1.76×** | 36.9 | **40.0** |
| ~31 800 | 750 tok/s | **1 400 tok/s** | **1.87×** | **37.2** | 36.8 |
| ~65 700 | 714 tok/s | **1 363 tok/s** | **1.91×** | 56.5 | **60.6** |

Wall time for a cold 65 k prompt: Strata 92.1 s, Talus 48.2 s.

Feed rate is flat across depth for Talus (1 050 → 1 363 tok/s) while Strata degrades from 564 to 714 and stays there; that is the main operational difference for an agent that re-prefills a long conversation on every tool call.

Decode is effectively a tie (0.99–1.16×, inside single-sample noise; the 56–61 tok/s cells reflect longer accepted draft runs, not a different engine speed class).

## Verdict

**Talus is deployed** as `talus-qwen.service` (user unit, port 18087, `--batch 2`, 131072 ctx). Strata stays installed and is a one-command rollback (`systemctl --user start strata-qwen.service` after stopping talus).

This is a **prefill win, not a decode win** — it makes long-context agent turns measurably faster, it does not make the model chattier.

## Known gaps in the Talus release (measured, not guessed)

- **Vision / OCR does not work through `talus-server`.** The engine accepts `--vision` and speaks the `GENI` image protocol, but the 0.1.3 server binary has no `mmproj`/vision code path and rejects image parts with `image input is not supported by this model`. A `vision` block in the run config is ignored. Workaround under test: keep Strata's Python `serve.server` (which implements the mmproj → `strata-vision` → `GENI` path) as the HTTP front-end and point it at `talus-cli --serve` as the engine.
- **No MTP head yet.** Neither arm had one, so the comparison is fair, but Talus can take one (`tools/mtp_fetch.py` + `mtp_pack.py` + `mtp_rt.py`, ~5 GB of `mtp.*` tensors from the Qwen BF16 checkpoint). Untested here.
- **`talus-cli` CLI traps:** the engine is started with `--serve`, *not* `--engine-protocol` (that name is only an alias in the help text and is rejected on the command line), and `--prefill <auto|N>` is mandatory in serve mode — without it the engine exits with `talus serve: needs --spec T and --prefill CHUNK`.

## Reproduction

```bash
# 1. ROCm SDK (no sudo, ~8 GiB)
pip3 install --target /mnt/c/ai/rocm-sdk \
  --extra-index-url https://nightly.repo.amd.com/rocm/whl-next/ \
  "rocm[libraries,devel,device-gfx1151]==10.2.0a20261014"
ln -sfn "$(PYTHONPATH=/mnt/c/ai/rocm-sdk python3 /mnt/c/ai/rocm-sdk/bin/rocm-sdk path --root)" \
  ~/Projekty/talus-dist/talus-v0.1.3-linux-x86_64-gfx1151/rocm-sdk

# 2. run config (engine args mirror the production Strata config)
#    exe = <release>/bin/talus-cli
#    args = --pack <pack> --native <gguf shard 1> --expert-profile <release>/data/expert-profile.bin
#           --expert-cache 17714 --prefill auto --spec 4 --spec-min-p 0.5 --max-context 131072
#           --kv int8 --kv-resident 32768 --resident-budget-gib 55 --vram-reserve-mib 700
#           --batch 2 --serve
#    lib_dirs = <release>/bin, <rocm-sdk>/lib, <rocm-sdk>/lib/rocm_sysdeps/lib, <rocm-sdk>/lib/llvm/lib

# 3. shipped env switches (these turn on prompt paths that are off in Strata's code defaults)
export STRATA_PF_FUSED=1 STRATA_PF_GEMM=1 STRATA_HC_UPMIX=1 STRATA_PA_FAST=1 \
       STRATA_HIP_WMMA=1 STRATA_SELECT_WMMA=1 STRATA_HC_Q8=1 \
       STRATA_PF_SWITCH_MIN_T=0 STRATA_PREFILL_STREAM_MIN=128

# 4. serve + measure
<release>/bin/talus-server --config talus-config.json --host 127.0.0.1 --port 18087
python3 bench_v2.py talus http://127.0.0.1:18087 2000,8000,32000,65536
```

Raw data: `records/talus-bench-20261104/bench_talus2.json`, `records/talus-bench-20261104/bench_strata2.json`.
