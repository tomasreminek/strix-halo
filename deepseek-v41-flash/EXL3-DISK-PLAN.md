# EXL3 space plan — what can be deleted to make room

Written 2026-10-22, alongside `MAYA-AMD-RESULTS.md` §8.5.

Goal: be able to download and test
`vcruz305/DSV4.1-Flash-1017-SAGE-EXL3-1.62bpw` (**326.57 GB**) on this box,
while keeping Hermes/Telegram, DSH on `:18095` and (later) production Strata
on `:18087` alive.

**Nothing here has been deleted.** This is a proposal with the measured sizes.

---

## 1. The storage layout — read this first, it changes the answer

The three filesystems are **not** one pool. They are separate partitions of the
same physical NVMe, and each has its own free-space pool:

```text
/dev/nvme0n1p4   582.6 G   ntfs   /mnt/data     17.82 GB free   98 %
/dev/nvme0n1p3      1 T   ntfs   /mnt/c       197.13 GB free   83 %   (mounted at /mnt/windows)
/dev/nvme0n1p6   296 G    ext4   /            45.95 GB free   85 %
/dev/nvme0n1p5   1000 M   ntfs   (not mounted)
/dev/sda1          1.9 T  exfat  (not mounted)
```

Two consequences that matter:

1. **Freeing space on `/mnt/c` does not help `/mnt/data`.** They share a disk
   but not a filesystem. The XS set lives on `/mnt/data` and EXL3 must land
   somewhere with **326.57 GB contiguous free** — that is `/mnt/c` (or `/`,
   if enough is freed there), *not* `/mnt/data` as it stands.
2. `/mnt/data` is at 98 % and cannot take EXL3 at all in its current state.
   Its 17.8 GB free is the XS reserve (see §2).

`sda1` is a **1.9 TB exFAT** disk, currently unmounted. It is by far the
largest single pool on the machine and is the natural home for EXL3 — with
the caveat that exFAT has no Unix permissions and no sparse-file support.
Nothing on the box currently depends on it.

**Total free right now across all mounted pools: ≈ 261 GB. EXL3 needs
326.57 GB. We are ≈ 66 GB short even before the safety margin.**

---

## 2. What is on disk right now, and who needs it

### `/mnt/data` (582.6 G, 17.8 G free)

| Path | Size | Needed by | Verdict |
|---|---:|---|---|
| `AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/` | 262 G | **Maya-XS download in flight** (280.88 GB total, 24 GB done at 17:41) | **KEEP** |
| `AI-Models/ComfyUI/models/` | 87 G | ComfyUI (LTX / diffusion / LoRA / VAE) — service `disabled` + `inactive` | candidate |
| `AI-Models/qwen38-flash-next-ngram.hgn` | 48 G | nothing currently references it (only old bench CSVs mention "ngram") | candidate |
| `AI-Models/Qwen-Image-2.1-Uncensored-GGUF` | 18 G | image generation, no active service | candidate |
| `AI-Models/Halogen-Qwen38-Flash-Next` | 2.3 G | `flashnext-server.sh` mounts it read-only → `qwen38-flashnext.service` | **KEEP** |
| `AI-Models/Qwen-ROCmFP4` | 1.6 G | ROCm FP4 experiments | candidate |
| `AI-Models/qwen38-flash-next-mtp.hgn` | 1.5 G | MTP variant of the same Halogen model | candidate (if the w4b variant is the live one) |
| `AI-Models/qwen38-flash-next-vision.hgn` | 857 M | vision variant | candidate (same) |
| `relocated/` | (already emptied) | — | free |

### `/mnt/c` (1 T, 197.1 G free)

| Path | Size | Needed by | Verdict |
|---|---:|---|---|
| `AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/Maya-S/` | 317 G | **Maya-S test — the next thing we do** | **KEEP until tested** |
| `AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/drafter-src/` | 16 G | the DSpark drafter source for Maya-S (`dspark.bin` 8.5 GB) | **KEEP until tested** |
| `AI-Models/Strata-Huihui-Abliterated-UD-IQ4_XS/` | 89 G | **production Strata** — `server_ablit.py:39` `MODEL_ROOT` | **KEEP** |
| `AI-Models/Strata-Unsloth-UD-IQ4_XS/` | 89 G | **nothing points here.** The live service uses the *Huihui-Abliterated* path; this is the un-abliterated twin | **candidate — 89 GB** |
| `AI-Models/ComfyUI_rw-models/` | 12 G | ComfyUI (read-write models) | candidate |
| `AI-Models/unsloth-llama-b10698-mix-rocm-gfx1151` | 1.6 G | old llama.cpp build | candidate |
| `AI-Models/unsloth-llama-b10715-mix-rocm-gfx1151` | 1.9 G | old llama.cpp build | candidate |
| `AI-Models/src`, `halofpx`, `strix-halo-llamacpp-v0.7.3/.6` | ~1.3 G | old sources/builds | candidate |
| `AI-Models/flashnext-bench`, `.hf-cache`, `.hf-home` | ~33 M | scratch | candidate |

### `/` (296 G, 45.9 G free)

`/home`, `/opt`, `/var`. Not a good home for a 326 GB model — the root
partition is the smallest and holds the OS, the toolchains and the ROCm
install. Moving EXL3 here is possible but wrong; it would also mean a
326 GB write to the same ext4 that already runs the Hermes gateway, the
build tree and `/mnt/data/toolchains`.

---

## 3. The plan

### Option A — the recommended one

**Move EXL3 to the unmounted 1.9 TB exFAT disk (`/dev/sda1`).**

```text
/mnt/exfat/AI-Models/EXL3-DSV4.1-Flash-1017-SAGE-1.62bpw/   ← 326.57 GB
```

Why:

- Zero deletions. Nothing that is currently needed is touched.
- 326.57 GB on a 1.9 TB disk leaves ~1.5 TB — room for a second copy, or for
  the 30 GB+ of extra tooling an EXL3 build needs.
- The two 101.5 GB shards (16 and 17 — the Engram tables, 6 tensors each)
  stay on one device, so there is no cross-filesystem read penalty at load.
- **The cost**: exFAT has no POSIX permissions, no symlinks, and no sparse
  files. The packer must be pointed at it explicitly; the safetensors
  loader must be able to read from it. `hf_transfer` / `huggingface_hub`
  can write there, but the umask/ownership has to be handled.

### Option B — free space on `/mnt/c` and keep everything in place

Free these, in this order:

| # | Delete | Frees | Risk |
|---|---|---:|---|
| 1 | `/mnt/c/AI-Models/Strata-Unsloth-UD-IQ4_XS/` (the un-abliterated twin of the live Strata) | **89 GB** | Low — nothing references it. Verify with `grep -r "Strata-Unsloth-UD-IQ4_XS" ~/Projekty ~/.config/systemd/user` first. |
| 2 | `/mnt/c/AI-Models/ComfyUI_rw-models/` | 12 GB | Low — ComfyUI is `disabled`/`inactive`; re-downloadable. |
| 3 | `/mnt/c/AI-Models/unsloth-llama-b10{698,715}-mix-*` + old `strix-halo-llamacpp-v0.7.*` | 3.7 GB | Low — superseded builds. |
| 4 | `/mnt/data/AI-Models/qwen38-flash-next-ngram.hgn` | **48 GB** | Low — no service points at it. |
| 5 | `/mnt/data/AI-Models/Qwen-Image-2.1-Uncensored-GGUF` | 18 GB | Low — no active service. |
| 6 | `/mnt/data/AI-Models/ComfyUI/models/loras` + `checkpoints` | 14.7 GB | Medium — creative assets, re-downloadable but slow. |
| 7 | `/mnt/data/AI-Models/qwen38-flash-next-{mtp,vision}.hgn` | 2.4 GB | Low — variants of the live Halogen model. |
| | **Total** | **≈ 188 GB** | |

That is not enough on its own: 197.13 GB free + 188 GB = **385 GB** ≥
326.57 GB. It *is* enough, with ~59 GB of slack — but only if the deletions
land on `/mnt/c` and `/mnt/data` in the right proportion, since the two
pools do not mix. Concretely, EXL3 must go on `/mnt/c`, so items 1–3
(**104.7 GB**) are the ones that count, giving 197.13 + 104.7 =
**301.8 GB** — still 25 GB short. Items 4–7 free space on `/mnt/data`,
which does **not** help unless EXL3 is split across both filesystems.
**That is the whole problem with Option B: the arithmetic only closes if
EXL3 lives on the exFAT disk, or if we delete Maya-S.**

### Option C — delete Maya-S after it has been tested

`Maya-S` (317 G) is the model we are about to test on the v1.1.22 engine.
Once Maya-S has been benchmarked and the results are in `strix-halo`, its
6 IQ2_XXS GGUF shards (317 GB) are the single biggest reclaimable block on
the box, and nothing else comes close.

```text
/mnt/c free after deleting Maya-S:  197.13 + 317 = 514 GB
EXL3 needs:                        326.57 GB
slack:                             187 GB
```

This is the **cleanest in-filesystem solution**, and it fits the user's own
statement that in the worst case Maya-S may go. The ordering matters:
**test Maya-S first, then delete it, then pull EXL3.** That way nothing is
lost before it has been measured.

`drafter-src` (16 GB) goes with it, unless the DSpark drafter is wanted for
a later comparison.

### Recommended sequence

```text
1. reboot                        (user action — GPU is wedged)
2. test Maya-S on v1.1.22        (needs Maya-S on disk → test BEFORE deleting)
3. test Maya-XS                  (needs the XS download to finish + SHA256)
4. restore Strata :18087
5. THEN: delete Maya-S (317 GB)  → /mnt/c has ~514 GB free
6. download EXL3 to /mnt/c       → 326.57 GB, ~187 GB slack
7. build/launch EXL3 via the in-tree HIP reader
```

Steps 1–4 are the user-approved priority order. Steps 5–7 are the EXL3
track, which the user explicitly deferred until after the Maya tests.

---

## 4. EXL3 facts verified from the model card and index

Retrieved 2026-10-22 from the HF API and the `model.safetensors.index.json`
(14.6 MB, 190 552 tensor names).

```text
repo:      vcruz305/DSV4.1-Flash-1017-SAGE-EXL3-1.62bpw
license:   MIT
base:      deepseek-ai/DeepSeek-V4.1-Flash-1017
format:    EXL3 (trellis), quant_method: exl3
profile:   1.62 bpw SAGE mixed-K
shards:    17, total 326 569 252 516 B = 326.57 GB
index:     model.safetensors.index.json (14 589 080 B)
config:    DeepseekV41ForCausalLM / model_type deepseek_v41
           40 layers, 384 routed + 1 shared expert, top-6
           hidden 5120, 64 heads, head_dim 512, MoE intermediate 2304
           vocab 129 280, max_position_embeddings 1 048 576
           rope yarn, factor 16
```

**The pack is self-contained.** It does **not** need the original 1017
Engram shards alongside it. The index contains 8 `engram.*` tensors
(`layers.1.engram.*` and `layers.14.engram.*` — `embed.weight`,
`k_weight`, `q_weight`, `wkv.weight` and their scales) and they live in
shards 16 and 17, which hold exactly **6 tensors each and are 101.5 GB
apiece** — that is where the 161 GB of Engram tables live, in EXL3 form.

> This **corrects** an earlier statement in `MAYA-AMD-RESULTS.md` §8, which
> said "the EXL3 shards must sit beside the original 1017 Engram shards".
> The upstream EXL3 pack carries its own Engram tables. There is no second
> 161 GB download.

Tensor census from the index:

```text
experts          189 186   (layers.N.ffn.experts.E.w{1,2,3}.{trellis,mul1,suh,svh})
layers/attn      1 003
other              343   (hc_attn_*, hc_ffn_*, image_* markers, mtp.*)
engram               8
embed/lm_head        8   (embed.weight, head.trellis, head.mul1/suh/svh, aligner.*)
total            190 552
```

**Measured quality claims (upstream, not reproduced here):** 94.52 % top-1
agreement with DeepSeek's official mixed FP8/FP4 release, mean KLD 0.0982;
**~112.9 GiB resident footprint** — sized for a 128 GB unified-memory
device.

**That resident footprint is the hard constraint.** This box has 124 GB of
physical RAM and ≈113 GB available, and must also keep Hermes/Telegram, DSH
on `:18095` and Strata alive. So:

- EXL3 at ~112.9 GiB resident is *the same order* as Maya-XS at 120.6 GB
  (upstream's figure). It is **tighter**, not looser.
- A cgroup `MemoryMax` around **113–116 GB** is the ceiling, and it leaves
  almost no headroom for the OS, the page cache and the Hermes gateway.
- **The EXL3 test and the Maya-XS test cannot both be resident at once.**
  They are mutually exclusive, and both compete with Strata.
- Whether the engine needs swap is a real open question — see §5.

---

## 5. What is still unknown about EXL3 on this box

- **Does the in-tree HIP EXL3 reader work at all?** `docs/EXL3_HIP.md`
  documents it as portable FP32 FMA — correctness-first, not a tuned
  AMD matrix path. `setup.py` currently **refuses** to install the EXL3
  components on HIP, so this needs either a patched installer or a manual
  pack + direct engine launch.
- **Upstream `exllamav3` cannot load this model at all** — it has
  `deepseek_v3/v4/v4_mtp/v4_vision` but **no `deepseek_v41.py`**
  (`MAYA-AMD-RESULTS.md` §8). So `exllamav3`'s ROCm port and its
  532-entry `gfx1151` WMMA tuning table are irrelevant to this checkpoint.
  Project Maya's own reader is the only path.
- **Version window.** Upstream states "ROCm 10 only, gfx1100+"; this box has
  **ROCm 7.14.1**. If Maya's reader has the same floor, EXL3 on HIP will not
  build here without a newer ROCm — which is a much larger undertaking than
  a 326 GB download.
- **No benchmark exists.** No token/s number for EXL3 on Strix Halo has been
  produced by anyone yet. Any number quoted for it in the community write-up
  would be a guess and must not be presented as a measurement.
- **The `1.62 bpw` label is about the *expert* weights only.** The
  non-expert tensors (attention, gates, Engram) are in a different
  precision, so "1.62 bpw" does not mean the model is 1.62 bits/param
  end-to-end. Do not use it to predict RAM usage.
- **Download time.** At the 19 MB/s measured for the XS shards, 326.57 GB is
  **≈ 4.8 hours**. At the ≈10 MB/s a naive 3-stream `curl` manages, it is
  **≈ 9 hours**. The chunked downloader (`~/.local/bin/xs-dl-chunked.py`)
  already implements the range/persistence pattern needed; it needs its file
  list swapped for the EXL3 one and the SHA256 table regenerated from the
  HF API.

---

## 6. Recommendation

**Mount `/dev/sda1` (1.9 TB exFAT) and put EXL3 there.** It needs no
deletions, no risk to the live models, and it leaves the 188 GB of
reclaimable space on `/mnt/c` available for something else later. If exFAT
turns out to be a problem for the packer, fall back to **Option C** —
test Maya-S, then delete it — rather than deleting live production models
to squeeze EXL3 onto `/mnt/c`.

Either way: **Maya-S and Maya-XS are tested first**, per the operator's
explicit priority.
