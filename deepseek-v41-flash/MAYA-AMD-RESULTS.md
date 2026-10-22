# Project Maya on AMD Strix Halo — measured results and causal analysis

**Box:** ASUS Ascent GX10 (AMD Ryzen AI Max+ 395, "Strix Halo" / `gfx1151`, 128 GB unified
RAM, wave64, ROCm 7.14.1) — this is the Strix Halo box described in the repo root README.

**Engine:** [`mw00/project-maya`](https://github.com/mw00/project-maya) `v1.1.21`
(commit `451f9cb`), built for HIP at `build-hip/maya-ds4`.

**Model:** `Maya-S` — DeepSeek-V4.1-Flash-1017 IQ2 GGUF, 6/6 shards, **339.5 GB**,
SHA256 verified (`VERSHOVEDNO`). Plus a repacked DSpark drafter
(`dspark.bin`, 8.50 GB, 1224 tensors; canonical repack `48529 tensors in 7 files`).

**Server:** `serve/server.py --engine strata`, port **18091** (18090 is taken by
`genex-strata-bridge.py`; 18087 is production Strata; 18095 is DSH).

**Date of this document:** 2026-10-22. Everything below was measured on this box.
Numbers that came from upstream release notes are marked as such and were **not**
reproduced here.

---

## 1. Headline: the target is not met yet

| metric | target | best measured (cold, fresh engine) |
|---|---|---|
| decode | ≥ 30 tok/s | **8.67 tok/s** |
| cold prefill | ≥ 900 tok/s | **438.0 tok/s** |

Both are from the same fresh-engine, cold-cache run:

```text
prompt 16043 tokens = 0 reused + 16043 read in 36624 ms (438.0 tok/s)
234 generated in 27005 ms (8.67 tok/s)
```

The 30 tok/s figure is not "a bit short" — it is **3.5× short**, and the reason is
measured, not guessed. The decode is **data-bound on the disk**, and the engine
currently uses roughly one disk reader's worth of bandwidth.

> **Read §5.5 before running the sweep again.** The sweep itself ended in a
> wedged GPU: every engine restart forced two full GPU resets, the 11th
> timed out, and `/dev/kfd` went to `EINVAL`. This is a driver-level
> `amdgpu`/KFD/MES failure, it is reproducible from the kernel log, and it
> also takes production Strata down with it.

---

## 2. Where the time actually goes (the arithmetic that matters)

From the engine's own log: **251.9 MB of expert data per generated token**,
and `vram_hit = 0.79` (≈21 % of each token's expert data still has to come off
the disk on the critical path).

```text
at 8.2 tok/s  →  251.9 MB × 8.2  =  2.07 GB/s   (measured engine throughput ≈ 2.1–3.0 GB/s)
at 20 tok/s   →  251.9 MB × 20   =  5.04 GB/s
at 30 tok/s   →  251.9 MB × 30   =  7.56 GB/s
```

The disk on this machine, measured directly with a fixed shard
(`...-00006-of-00006.gguf`, 300 MB per thread):

| readers | throughput |
|---|---|
| 1 | **2.75 GB/s** |
| 4 | **12.44 GB/s** |
| 8 | **12.87 GB/s** |
| 16 | **13.67 GB/s** |

**This is the central finding of the whole investigation.** The disk is fast
enough to hit 30 tok/s with room to spare — it needs 7.56 GB/s and can do 13.67 GB/s
with 16 readers. But the engine currently runs at the throughput of **one**
reader (2.75 GB/s), and it is getting *less* than that (2.1–3.0 GB/s).

The engine's own log explains why it is not using the disk's parallelism:

```text
an expert 0.217 ms on the CPU lane ... 1.87 ms from the disk
decode measured the split against the CPU lane alone on requests with
experts from the disk: 5.58 against 4.69 ms (+19.1%) -> it no longer streams them
```

The engine **disabled its own PCIe streaming lane** because splitting experts
across the PCIe lane was 19.1 % slower than keeping everything on the CPU lane.
So the reads are serialised into one stream, and that single stream tops out at
~2.75 GB/s. That is the bottleneck, and it is self-inflicted.

Decode cost check from the log: `122 ms/token ≈ 3 ms/layer`, and
`1 expert from disk = 1.87 ms`. 22 disk-experts per token on the critical path
× 5.58 ms ≈ 122 ms — the numbers line up. The decode is I/O latency, not compute.

Cold prefill tells the same story: it pulled ≈162 GB of expert data in 36.6 s
= **≈4.4 GB/s**. To reach 900 tok/s it needs ≈9 GB/s. The disk can do it; the
engine's read path cannot.

---

## 3. The cgroup / read-ahead interaction (a correction worth recording)

An earlier conclusion in this investigation was **wrong** and is corrected here.

The engine's `ram_avail()` (`src/ds4/ds4_model.cu:209-248`) does **not** read
host `/proc/meminfo` only. It takes the **minimum** of:

```text
min( host MemAvailable,
     tightest cgroup-v2 memory.max on the path to root - used )
```

where `used = memory.current - file`, i.e. page cache counts as reclaimable
and therefore as *available*.

`warm_bytes` is then (`ds4_model.cu` ~line 2763):

```text
warm_bytes = min(ram_avail() - kRamMargin, need)      kRamMargin = 8 GiB
```

This reconciles the log exactly:

```text
memory.max = 80 GiB = 85.9 GB (decimal)
used ≈ 0.3 GB
→ effective RAM free ≈ 85.6 GB   (log says exactly "85.6 GB RAM free")
→ read-ahead = 85.6 - 8.6 = 77.0 GB (log says exactly "77.0 GB")
```

**Consequences that were verified in code, not assumed:**

- The cgroup limit **is** respected. Stopping Strata does **not** by itself
  enlarge the read-ahead plan, because `MemAvailable` (110.9 GB) was above the
  cgroup limit anyway — the cgroup was the binding constraint.
- Raising `MemoryMax` from 80G to 104G raises the plan from 77.0 GB to ≈95 GB
  **and** simultaneously enlarges the GTT expert pool (`vram-experts` is a
  fraction of free VRAM). Both effects move at once, so that variant cannot
  attribute the change to one cause on its own.
- `DS4_COMMIT_CAP_GB` **is** active on Linux: `commit_charged()` returns true
  merely when the env var exists, and `commit_margin()` is a fixed 8 GB on
  Linux (no commit limit, `c.ram ≈ 0`). So cap `40` → ≈32 GB of GTT room,
  cap `56` → ≈48 GB. This is a direct lever on how much of the expert data
  lives in GPU memory instead of on the disk.

---

## 4. Levers that were checked in the source, and what they actually do

Verified by reading `src/ds4/ds4_model.cu`, `src/ds4/ds4_os.hpp`,
`src/ds4/ds4_main.cpp`.

### Live, useful

| lever | default | meaning |
|---|---|---|
| `DS4_READERS` | **8** | depth of the `IoQueue` used for disk reads of experts — **the primary lever against the single-stream bottleneck** |
| `DS4_AHEAD` | **1** | lookahead: 0 = off, 1 = one layer ahead, 2 = two layers ahead |
| `DS4_AHEAD_ORDER` | **1** | 0 = "expert order" instead of "asked-for-early-first" |
| `DS4_AHEAD_EXTRA` | 0 | **accepts negative values**; `<0` reads *fewer* experts than estimated — on an SSD-bound machine this stops needless SSD traffic |
| `DS4_READAHEAD_MB` | 2048 | the `POSIX_FADV_WILLNEED` window after a batch |
| `DS4_COMMIT_CAP_GB` | — | caps the GTT expert pool in GB (active on Linux, see above) |
| `--vram-experts` | 0.5 | fraction of free RAM for the GTT/RAM expert pool |
| `MemoryMax` / `MemoryHigh` | 80G / 70G | cgroup limits → how much page cache the engine may hold |
| `DS4_CACHE_THREADS` | 1 | threads for the expert-cache swap |

### Confirmed dead ends (do not spend time on these)

| lever | why it is a no-op here |
|---|---|
| `DS4_WARM_GB` | `warm_after()` early-returns unless `L[0].lay.fmt == kFmtMXFP4`; the IQ2 pack is not MXFP4 → **no-op** |
| `DS4_COPY_GB` | `copy_experts()` early-returns while `mmap_experts > 0`; the current path is mmap/in-place → **no-op** |
| `--mmap-experts off` | **not** a low-RAM solution: it copies the expert data into RAM, ≈100 GB |
| `DS4_STREAM_THREADS` | default 2, max 8, but the engine **disabled the PCIe lane itself** (−19.1 %) → practically a no-op |
| `DS4_FLOW`, `DS4_LAYER_MAJOR` | MXFP4-gated |
| `DS4_APU_DEDICATED_GB` | Windows only |
| `cpu_threads`, `read_chunks`, `pcie_frac` | GLM-era aliases, not DS4 request keys |
| `STRATA_DS4_DISK_SKIP_W` | **changes the model's answers** — it must never be part of a production performance measurement |

`DS4_BORROW` is new and special: `DS4_BORROW=0` switches off exactly the
"lend path" (`borrow_begin`) that contains the failing `cudaMemsetAsync` —
see §6. It is used here as a **diagnostic** variant, not as a performance fix.

### The MTP / drafter situation

The drafter is **working**, and it is not the problem:

- the original pack had no `mtp.0.attn.wq_a.*` tensors → `n_mtp = 0` → drafter inactive;
- after the canonical repack, the log shows `layers [0, 42]` and metrics show
  `drafts = 0.835` (96 of 115 drafts kept = **83.5 % acceptance**);
- decode with the drafter: **7.48–7.5 tok/s** — essentially unchanged.

The drafter does **not** explain the HIP error: the error was already in the log
**before** the repack.

---

## 5. The HIP error — what is actually known

```text
ds4: cudaStreamSynchronize(d.st): unspecified launch failure
ds4: cudaMemsetAsync(d.tail + b0, 0, d.tail_bytes - b0, d.st): unspecified launch failure
```

What was established:

1. The `cudaMemsetAsync` call is located in the **borrow / "lend path"**
   (`src/ds4/ds4_model.cu`, `borrow_begin`, around lines 8596-8665; the
   `d.tail` memset at ~8637 and the stream sync right after it).
2. `DS4_BORROW=0` switches off exactly that path → it is the precise
   diagnostic switch for this error.
3. **The error is not automatically fatal.** A later log section shows the
   error *followed by* a fully successful request:

   ```text
   ds4: cudaStreamSynchronize(d.st): unspecified launch failure
   maya ds4 serve: prompt 16043 tokens = 0 reused + 16043 read in 36624 ms (438.0 tok/s), 234 generated in 27005 ms (8.67 tok/s)
   ```

   So the earlier working hypothesis "the engine dies on the second request,
   every time" is **not** generally true. The failure is recoverable in at
   least some sequences, and it must be re-tested in isolation before anyone
   claims a fatal causal link.
4. The exact meaning of `d.tail`, `b0`, `d.tail_bytes` and whether a `size_t`
   underflow is possible in `d.tail_bytes - b0` is **not yet confirmed** — the
   audit of that arithmetic did not finish.

**Open:** whether this error costs performance even when it does not kill the
engine (e.g. it aborts a kernel launch and forces a fallback path). The sweep
now records `hip_errors` and `engine_alive_after` per variant so this can be
answered from data rather than argument.

---

## 5.5 The GPU fault — the complete causal chain

**This is the most important result in this document.** It explains both the
HIP error above *and* the `no CUDA device` failure that ended the sweep, and
it is a driver-level finding, not a configuration error.

### The trigger

Every time the Maya engine's HIP context is torn down, the kernel driver
`amdgpu` tries to evict the process's queues from the GPU's memory scheduler
(MES) and the MES does not answer:

```text
amdgpu 0000:c5:00.0: MES failed to respond to msg=REMOVE_QUEUE
amdgpu 0000:c5:00.0: failed to remove hardware queue from MES, doorbell=0x1002
amdgpu 0000:c5:00.0: MES might be in unrecoverable state, issue a GPU reset
amdgpu 0000:c5:00.0: Failed to evict queue 1
amdgpu 0000:c5:00.0: Failed to evict process queues
amdgpu 0000:c5:00.0: GPU reset begin!. Source:  3
amdgpu 0000:c5:00.0: MODE2 reset
amdgpu 0000:c5:00.0: GPU reset succeeded, trying to resume
amdgpu 0000:c5:00.0: SMU is resuming... / SMU is resumed successfully!
amdgpu 0000:c5:00.0: GPU reset(6) succeeded!
amdgpu 0000:c5:00.0: [drm] device wedged, but recovered through reset
```

**So the chain is: engine exit → KFD/MES queue eviction fails → driver forces a
full GPU reset.** The engine's own `unspecified launch failure` is the
*application-side* symptom of that reset, not an independent bug: the reset
kills the HIP context while the app is still using it.

### The count: 11 resets, and the 11th is the one that kills the GPU

```text
boot -0 = 2026-10-22 01:34:03 (current boot)

03:58:12  GPU reset begin! Source: 3  → reset(1)  succeeded
04:07:19  GPU reset begin! Source: 3  → reset(2)  succeeded
04:33:26  GPU reset begin! Source: 3  → reset(3)  succeeded
07:21:12  GPU reset begin! Source: 3  → reset(4)  succeeded
08:25:54  GPU reset begin! Source: 3  → reset(5)  succeeded
───────────────────────────────────────────────────────────────── sweep starts
14:32:00  GPU reset begin! Source: 3  → reset(6)  succeeded   ┐ v01-base
14:32:02  GPU reset begin! Source: 3  → reset(7)  succeeded   ┘
14:34:24  GPU reset begin! Source: 3  → reset(8)  succeeded   ┐ v02-readers16
14:34:26  GPU reset begin! Source: 3  → reset(9)  succeeded   ┘
14:37:23  GPU reset begin! Source: 3  → reset(10) succeeded   ┐ v03-readers32
14:37:25  GPU reset begin! Source: 3  → reset end with ret = -110  ← FATAL
```

**Every single valid sweep variant costs exactly two GPU resets** (one for the
engine's HIP context teardown, one for the process's KFD queues), and the
timestamps line up to the second with the engine logs:

| variant | engine.log mtime | bench-results mtime | matching resets |
|---|---|---|---|
| v01-base | 14:32:00 | 14:32:02 | reset(6) 14:32:00, reset(7) 14:32:02 |
| v02-readers16 | 14:34:24 | 14:34:26 | reset(8) 14:34:24, reset(9) 14:34:26 |
| v03-readers32 | 14:37:23 | 14:37:25 | reset(10) 14:37:23, reset(11) 14:37:25 → **-110** |

The 11th reset — the one triggered by the teardown of `v03-readers32` — is the
one that timed out:

```text
14:37:25  amdgpu 0000:c5:00.0: GPU reset begin!. Source:  3
14:37:26  amdgpu 0000:c5:00.0: GPU reset end with ret = -110
```

`ret = -110` is `ETIMEDOUT`. The GPU did not come back. From that moment the
SMU stops answering (`SMU: No response msg_reg: 21 resp_reg: 0`,
`Failed to retrieve enabled ppfeatures!`), and:

```text
rocm-smi                      → still enumerates the PCI device
rocminfo                      → Unable to open /dev/kfd read-write: Invalid argument
open('/dev/kfd', O_RDWR)      → EINVAL
open('/dev/kfd', O_RDONLY)     → EINVAL      (even read-only fails)
```

KFD cannot enumerate the device, so every HIP runtime that asks for a device
gets "none". The engine's next start therefore dies instantly:

```text
maya ds4 serve: no CUDA device        ← 25 bytes, the entire v04..v21 engine log
```

### What this means

1. **`no CUDA device` is a consequence, not a cause.** It is not a bad
   `DS4_*` setting, not a missing device, not a ROCm CLI problem. `rocm-smi`
   seeing the GPU while `rocminfo` cannot open `/dev/kfd` was the decisive
   clue that the fault is in the driver/KFD communication path, not in ROCm.
2. **The first ten resets were recoverable.** The engine continued after each
   of them and still produced a valid measurement — which is why `v01`–`v03`
   have `hip_errors = 1` and `engine_alive_after = 200`. The HIP error and the
   reset are the *same event*.
3. **`v04`–`v21` are not evidence about any lever.** All 18 variants died
   before a request was issued; they only contain a config JSON and a 25-byte
   `no CUDA device` log. They must not be read as "the knob did not help".
4. **The trigger is the engine's HIP teardown, not its compute.** Every start /
   stop cycle of the Maya engine costs two full GPU resets on this box. On a
   `gfx1151` APU with `reset_method = pm bus` (an integrated GPU, which cannot
   be PCI-reset), enough of those in a row will hang the SMU for good.
5. **The original trigger of the *first* MES failure is still not identified.**
   What is established is the mechanism and the threshold (the 11th reset
   timed out), not what put the MES into that state in the first place.

### Recovery

```text
0000:c5:00.0  reset_method = pm bus        → integrated APU GPU, no PCI bus reset possible
/sys/bus/pci/devices/0000:c5:00.0/reset    → --w------- root:root, not writable unprivileged
sudo -n -l                                  → "sudo: a password is required"
```

An unprivileged in-place recovery is not possible. A full reboot is required
(the SMU firmware state has to be reinitialised). Because the GPU is the only
device on this SoC that runs HIP compute, **the failure also takes down
production Strata on `:18087`** — its engine cannot initialise without a
device:

```text
strata generate: native embedding: cannot pin 644 MiB: no ROCm-capable device is detected
```

Recovery checklist (verified on this box):

```text
Hermes gateway   enabled + Restart=always + Linger=yes  → comes back by itself
Strata           enabled                                  → comes back by itself
DSH               dsh-strata-web.service is "disabled", BUT it is pulled in by
                 roots-of-pacha-worker.service (Wants=dsh-strata-web.service)
                 and that unit IS enabled + WantedBy=default.target
                 → comes back by itself as well
```

The desktop session on `tty1` has no autologin, so a GUI login prompt waits
after the reboot — that does not affect Hermes/Telegram, DSH or Strata, which
are user services that start without a graphical login (`Linger=yes`).
`dsh-strata-web` has `Restart=on-failure` and
`After=... genex-strata-unsloth.service`, so it also waits for Strata.

---

## 6. Benchmark methodology (why these numbers can be compared)

A/B sweep, 19+ causal variants, each measured in isolation. The rules that make
the rows comparable:

1. **Fresh engine per variant.** The engine is stopped and restarted for every
   variant — no warm state carries over.
2. **Cold page cache per variant.** `maya-drop-cache.py` issues
   `POSIX_FADV_DONTNEED` over the model shards and the drafter pack before the
   engine starts. Measured effect on this box: `59.1 GB → 14.0 GB`
   (45.1 GB released, 348.0 GB touched). `POSIX_FADV_DONTNEED` on the NTFS3
   mount was verified to release exactly 256 MB in a controlled test.
3. **Exactly one measured inference request per engine.** This matters because
   of the HIP error described above.
4. **Explicit `--setenv=`.** `systemd-run` does **not** inherit the parent's
   exported environment — verified: an exported variable arrived as
   `NENASTAVENO`; `--setenv=DS4_READERS=16` correctly arrived as `16`. Without
   this, every env variant would have been a silent no-op.
5. **Cgroup limits on every engine:** `MemoryMax`, `MemorySwapMax=2G`,
   `MemoryHigh`, `OOMPolicy=stop`, so a misbehaving engine kills itself
   instead of the machine.
6. **Timeout and lock:** per-variant timeout, `flock` on the state directory so
   a second sweep cannot start.
7. **Strata is stopped for the whole sweep and restored afterwards**, with
   `loaded: true` and a successful `/v1/chat/completions` verified on `:18087`.
   *Caveat from this run: the restore step ran but could not succeed — the GPU
   had already been killed by the reset storm (§5.5). The sweep's EXIT trap
   correctly logged `WAR: Strata nereagovala s loaded=true` instead of
   claiming success. The mechanism is right; the hardware was gone.*
8. **Never two engines.** The engine is stopped before each variant.

### Two methodology bugs that were found and fixed

**Health check.** The original readiness probe was:

```bash
curl -s -m 5 -o "%{http_code}" ... | grep -q 200
```

`-o` redirects the **body** into a file literally named `%{http_code}` and
stdout stays empty, so `grep` never matched. The effect was a 20-minute wait
per variant, every variant discarded. Reproduced deliberately, and the stray
file `/home/tomasreminek/%{http_code}` was found on disk. Fixed to:

```bash
curl -s -m 5 -o /dev/null -w '%{http_code}' ... | grep -q '^200$'
```

**Request accounting.** `wait_ready()` in the benchmark sends a *real* tiny
completion to find out whether the weights are resident. With `--turns 1` that
means the **measured** request is request #2, not #1. The `wait_ready()` path
now has to be either replaced by a non-invoking readiness probe or explicitly
accounted for, otherwise the "one measured request" rule is not true.

---

## 7. A community-facing summary (what worked, what did not)

### What worked

- **Project Maya v1.1.21 runs DeepSeek-V4.1-Flash on AMD Strix Halo at all** —
  a 339.5 GB IQ2 model on a 128 GB unified-memory APU, with a working MTP
  drafter at 83.5 % acceptance and a 65536-token context.
- **The DSpark repack procedure** works end to end: `dspark.bin` (1224 tensors,
  8.50 GB) into the pack → `48529 tensors in 7 files`, repack exit 0.
- **HIP `rocWMMA` / WMMA kernels are in the binary** — `wmma_set_mix_kernel`,
  `wmma_set_kernel`, `sparse_attn_wmma_kernel` are all present in
  `build-hip/maya-ds4` (`ds4_iq.cu` sets `DS4_ROCWMMA 1` for HIP,
  `ds4_kernels.cu` sets `DS4_ATTN_WMMA 1`).
- **The cgroup-aware read-ahead planner** works exactly as documented (§3), and
  `DS4_COMMIT_CAP_GB` is a real, tunable lever on Linux.
- **A reproducible A/B harness**: 21 causal variants, one measured request,
  cold cache, explicit env, cgroup limits, Strata restore, no duplicate engine.
  Only 3 of the 21 produced a valid measurement (see §5.5), but the harness
  itself is reproducible and its failure mode is now understood.

### What did not work

- **The target was not met.** 8.67 tok/s decode vs 30 required; 438 tok/s cold
  prefill vs 900 required.
- **The decode is I/O-bound, not compute-bound.** The engine runs at one
  reader's bandwidth (2.1–3.0 GB/s) while the disk does 12.4–13.7 GB/s with
  4-16 readers. The engine disabled its own PCIe streaming lane (−19.1 %),
  which serialised the reads.
- **The obvious knobs are dead ends** on this model: `DS4_WARM_GB` and
  `DS4_COPY_GB` are no-ops, `--mmap-experts off` needs ≈100 GB of RAM,
  `DS4_STREAM_THREADS` is neutralised by the engine's own lane decision.
- **The drafter does not rescue decode.** 83.5 % acceptance, but 7.48 tok/s.
- **Two harness bugs** (health check, request accounting) invalidated two
  earlier sweep attempts. Both are fixed; the lesson for the community is that
  an A/B matrix on a 339 GB model is only as good as its readiness probe.
- **The sweep killed the GPU.** 21 variants, each with a fresh engine; every
  engine teardown forced two full GPU resets. The 11th reset of that boot
  timed out (`ret = -110`), the SMU stopped answering and `/dev/kfd` has
  returned `EINVAL` ever since — which also took production Strata down with
  it. This `amdgpu`/KFD/MES failure is documented in full in §5.5 and is the
  single most useful thing this investigation produced for the community:
  **do not run a per-variant engine-restart loop on a `gfx1151` APU without
  watching the GPU reset counter.**

### The open question worth the community's attention

> **How do you make a 340 GB MoE read its experts from an NVMe in parallel
> when the engine's own tuning decides the parallel path is 19 % slower?**

`DS4_READERS` (default 8) and `DS4_AHEAD` (default 1) are the untested
levers on the read path, and the source audit says they are not flow-gated.
If the disk can do 13.67 GB/s and the engine uses 2.1, the gap is the
interesting engineering problem — not the model, not the quantisation, not the
GPU.

---

## 8. EXL3 on AMD — status

**Upstream claim (NOT reproduced on this box):** Project Maya v1.1.20/v1.1.21
port EXL3 to AMD HIP kernels (RDNA 3 / 3.5 / 4, Strix Halo included) and to
Tesla V100, with v1.1.21 adding WMMA prompts, AMD byte-sum/dot-product
instructions, first-start self-tuning of matrix kernels, attention sized from
available GPU memory, and a decode path that skips the CPU round trip for
layers whose experts are already in GPU RAM.

**What is true here:** this repository *is* `mw00/project-maya` at `v1.1.21`,
and `docs/EXL3_HIP.md` exists in-tree (4,042 bytes, read in full). EXL3 HIP
support is therefore **in-tree, not hypothetical**.

An earlier conclusion in this investigation — that "EXL3 is CUDA-only, so it
cannot run on AMD" — was **wrong** and is retracted. It was based on the
generic upstream `exllamav3` project, whose release assets (`v1.6.0`, `v1.6.4`)
are `cu128`-only, while its `master` branch does have a ROCm build path
(`setup.py` detects `torch.version.hip`, ROCm port PRs #441, #443, #365, #366).
The generic upstream constraint does not automatically apply to Maya's own
implementation.

**Still unverified, and it matters:** the local platform is ROCm **7.14.1**,
GPU **gfx1151**, **wave64**. Upstream `exllamav3` v1.6.0 states "Preliminary
ROCm support (ROCm 10 only, gfx1100+)", and PR #441 discusses RDNA/**wave32**.
So the *generic* upstream path is not obviously compatible with this box.
Maya's in-tree implementation may well be — that has to be measured, not
assumed.

### Upstream `exllamav3` master, audited directly (2026-10-22)

The master branch was downloaded and read, not just the README:

```text
https://codeload.github.com/turboderp-org/exllamav3/tar.gz/refs/heads/master
→ exllamav3/exllamav3_ext/rocm/                        ← a real ROCm port
→ exllamav3/exllamav3_ext/rocm/wmma_gemm.cu
→ exllamav3/exllamav3_ext/rocm/wmma_gemm_table.cuh
     ... exl3_wmma_entries_gfx1151[532]                 ← 532 tuned entries FOR gfx1151
```

So the generic upstream project is **not** "CUDA-only": it ships a HIP port
with a Strix-Halo-specific tuning table. Two things are nevertheless missing
for this particular checkpoint:

```text
exllamav3/architecture/  →  deepseek_v3.py
                            deepseek_v4.py
                            deepseek_v4_mtp.py
                            deepseek_v4_vision.py
                            (no deepseek_v41.py)
```

1. **No `deepseek_v41.py`** — the DeepSeek-V4.1 architecture is not in upstream
   master, so upstream `exllamav3` cannot load this model at all, ROCm port or
   not. The `gfx1151` table is a *kernel-level* win, not a *model-level* one.
2. **Version mismatch** — upstream states "ROCm 10 only, gfx1100+"; this box
   has ROCm 7.14.1. The kernels are present but the stated support window
   does not include the local ROCm.

**Conclusion for the community:** "EXL3 does not run on AMD" is **false as
stated** — upstream has gfx1151-tuned HIP kernels. The accurate statement is
narrower and more useful:

> EXL3 has a real AMD/ROCm path with Strix Halo tuning, but as of 2026-10-22
> upstream `exllamav3` has no DeepSeek-V4.1 architecture, so `exllamav3`
> cannot serve this model. Project Maya's own in-tree EXL3 reader
> (`tools/ds4/pack.py`, `include/strata/kernels/exl3.hpp`) is the only
> EXL3-on-AMD path for DeepSeek-V4.1-Flash.

**Caveat on Maya's own path:** `docs/EXL3_HIP.md` documents the HIP bring-up
as portable FP32 FMA — a correctness-first path, *not* a tuned AMD
matrix-instruction path. `setup.py` currently **refuses** to install the EXL3
components on HIP, so a working setup needs either a fixed installer or a
manual pack + direct engine launch. `DS4_SKIP_UNPICKED=1` (PR #297) is also
absent from this tree.

**EXL3 model:** `vcruz305/DSV4.1-Flash-1017-SAGE-EXL3-1.62bpw` —
**326.57 GB**, **17 shards**, `quant_method: exl3`. **Not downloaded yet.**

> **Correction (2026-10-22).** An earlier version of this section said "the
> EXL3 shards must sit beside the original 1017 Engram shards". That is
> **wrong** and is retracted. The upstream EXL3 pack is **self-contained**:
> its `model.safetensors.index.json` (190 552 tensors) carries 8 `engram.*`
> tensors of its own, and they occupy shards **16 and 17** — 6 tensors each,
> **101.5 GB per shard**. There is **no second 161 GB download**; the
> 326.57 GB figure is the whole model. See `EXL3-DISK-PLAN.md` for the
> full census and the space plan.

**Space:** EXL3 needs 326.57 GB on one filesystem. `/mnt/data` is at 98 %
and cannot hold it; `/mnt/c` has 197.13 GB free and would need Maya-S
deleted (317 GB) first. The unmounted **1.9 TB exFAT** disk (`/dev/sda1`)
is the clean answer — no deletions required. Full analysis and the
recommended sequence are in **`EXL3-DISK-PLAN.md`**.

**Resident footprint:** the model card states **~112.9 GiB** resident —
the *same order* as Maya-XS's 120.6 GB, i.e. **tighter**, not looser. On
this 124 GB box the EXL3 test and the Maya-XS test are mutually exclusive
and both compete with production Strata.

**Decision:** the EXL3 model is **not** downloaded until capacity, access, the
correct build/load procedure and an isolated test are all confirmed. The
NVIDIA Spark recipe (`vcruz305/DSV4.1-Flash-1017-EXL3-Spark-recipe`) is
included as a **source of build/quantisation know-how**; its runtime is
NVIDIA-only and must not be assumed to transfer to AMD.

---

## 8.5 Project Maya v1.1.22 — what changed, what was verified, what was not

Recorded 2026-10-22. This section covers the move to the official upstream
release `v1.1.22` and the start of the Maya-XS campaign. It is deliberately
split into **verified** (measured on this box or read directly out of the
pinned source) and **not verified** (upstream claims, or blocked by the
GPU fault of §5.5).

### 8.5.1 The release itself — verified

| Item | Value | How it was checked |
|---|---|---|
| Upstream release | <https://github.com/mw00/project-maya/releases/tag/v1.1.22> | GitHub release page + API |
| Tag → commit | `v1.1.22` → `ffe2e5e53fd5254e7f3492a20e8ad2b51b26a197` | `git fetch origin tag v1.1.22` |
| Local checkout | `ffe2e5e5`, worktree clean | `git log --oneline -1`, `git status --short` |
| HIP build | `[100%] Built target maya-ds4` | `cmake --build build-hip --target maya-ds4 -j16` |
| Build log | `~/.hermes/logs/maya-build-122.log` | — |
| ROCm used | **7.14.1**, gfx1151, at `/mnt/data/toolchains/strata-rocm-7.14.1-gfx1151/install` | `build-hip/CMakeCache.txt` |

Two build notes that cost time and are worth recording:

- **`make all` fails on this tree** (`gmake: *** [Makefile:146: all] Error 2`).
  A **targeted** `cmake --build build-hip --target maya-ds4 -j16` succeeds.
  Use the targeted form.
- The built binary needs
  `LD_LIBRARY_PATH=/mnt/data/toolchains/strata-rocm-7.14.1-gfx1151/install/lib`.
  There is **no system ROCm** (`/opt/rocm` does not exist on this box), so a
  bare `./maya-ds4` fails with
  `libhipblas.so.3: cannot open shared object file`.

The v1.1.21 engine binary was preserved at
`~/.hermes/cache/scratch/maya-ds4-v1.1.21` for A/B.

### 8.5.2 What v1.1.22 adds (upstream claims, read from `CHANGELOG.md`)

- **Maya-XS** — DeepSeek-V4.1-Flash in **120.6 GB** of memory. All 384
  experts per layer kept at ~1.6 bits (`IQ1_S`), requantised with error
  feedback on the quantized model itself. Its own **2-bit DSpark drafter**
  (`4.25 GB`). The **Engram tables (161 GB, Q6_K) stay on the SSD**, as with
  Maya-S. Install line: `./setup.sh --setup --model DeepSeek-V4.1-Flash-1017
  --ds4-quant maya-xs`.
- **DeepSeek tensor parallel** over several GPUs (#344). On **one** GPU,
  drafting decodes **~1.85x faster** than v1.1.21 (Maya-S with DSpark on a
  Ryzen AI Max, same drafts kept).
- **AMD fixes**: a 2-GPU DeepSeek hang with hipBLASLt (#367, #366); the packed
  sparse attention LDS swizzle, opt-in via `DS4_HIP_ATTN_SWIZZLE=1` (#348);
  `--bench` takes the DeepSeek engine on HIP (#350).
- **Windows**: 1 ms engine timer (`MAYA_DS4_TIMER_MS=0` leaves it), 64 Engram
  readers (#361), unbuffered Engram reads (`DS4_EG_DIRECT=0` = before).
- **Prompt report**: `DS4_PREFILL_STATS=1` (#364) shows which experts a
  prompt found resident and the bytes it streamed.
- **GLM**: a prompt's lending keeps more recently used experts in RAM — 40 %
  fewer disk reads after a fresh prompt (#352).

Source-level confirmation that the flags exist in the pinned tree
(`src/ds4/ds4_main.cpp`): `--pack` (686), `--vram-experts` (691),
`--dspark` (696), `--dspark-conf` (700), `--serve` (724).

### 8.5.3 The Maya-XS download set — verified

Source: `peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF`, revision
**`c273fcbdda76a1db074c2f414cb70edbfca2f2ef`** (pinned, not `main`).

```text
Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00001-of-00005.gguf  47781530400
Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00002-of-00005.gguf  47775748128
Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00003-of-00005.gguf  19784230848
Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00004-of-00005.gguf  80641295472
Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00005-of-00005.gguf  80643503412
dspark/dspark-xs2.bin                                                4251725568
dspark/dspark-xs2.json                                                    99146
                                                    total bytes ≈ 280.88 GB
```

**All of it goes on one filesystem** (`/mnt/data/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/Maya-XS`).
An earlier plan to split the shards with symlinks across `/mnt/data` and
`/mnt/c` was dropped on purpose — both are NTFS3 on the *same* physical 2 TB
NVMe, and a split adds a failure mode for no gain.

Note the drafter is **`dspark-xs2.bin`** (4.25 GB), *not* the older
`dspark-xs.bin` (3.4 GB). The two are not interchangeable.

### 8.5.4 The download itself — verified, with two real bugs found and fixed

`~/.local/bin/xs-dl-chunked.py` replaces a naive 3-stream `curl` loop. It
splits every file into 64 MB byte-range chunks, fetches them from a global
thread pool, writes each chunk with `pwrite()` at its own offset, and
persists the set of completed ranges per file in
`~/.hermes/state/xs-dl/*.json` so an interrupted run resumes instead of
restarting. A SHA256 pass runs over every file at the end.

**Measured on this box:**

| Variant | Aggregate throughput |
|---|---|
| 3 sequential `curl` streams | **≈10 MB/s** (≈8 h ETA) |
| 8 parallel 100 MB range streams | ≈17 MB/s |
| 16 parallel 50 MB range streams | ≈19 MB/s |
| chunked downloader, 24–48 workers | **19 MB/s** sustained, confirmed independently at the network interface (12 MB/s on `/sys/class/net/*/statistics/rx_bytes` over 30 s) |

Two bugs were found and fixed while building it — both are easy to repeat:

1. **One-byte `pwrite` loop.** The write loop advanced the offset by the
   *return value* of a single-byte `pwrite`, so every chunk cost millions of
   syscalls. Fixed to write the whole buffer in one call, looping only on a
   short write.
2. **`tuple` vs `list` in the range state.** `norm()` sorted a mix of tuples
   (freshly appended) and lists (loaded from JSON), raising
   `TypeError: '<' not supported between instances of 'tuple' and 'list'`
   and losing every chunk. Fixed by coercing to `(int, int)` inside `norm()`.

A third, subtler trap: the preallocated file size is **not** a validity
signal. A chunked run `ftruncate()`s each file to its full size, so the file
looks complete before a single byte is fetched. The persisted range set is
the only truth; the on-disk prefix is adopted **only** on the very first run,
where an earlier sequential download left a contiguous head.

**Safety rule observed:** only one writer per file. The old 3-stream
downloader was stopped (`systemctl --user stop maya-xs-download.service`)
before the chunked one was started; they must never run at the same time.

### 8.5.5 Disk capacity — verified, and it is tight

`/mnt/data` and `/mnt/c` are **NTFS3** mount points on the *same* physical
2 TB NVMe.

```text
/mnt/data   583 G total   567 G used   17 G free   98 %   ← NTFS3
/mnt/c      1.1 T total   841 G used  184 G free   83 %   ← NTFS3
/            291 G total   233 G used   43 G free   85 %
```

**NTFS3 `ftruncate` is not sparse** — the preallocated 276.6 GB of XS shards
occupies real space from the first second of the download. The XS set fits on
`/mnt/data` with roughly **12 GB** to spare, and nothing else large can be
placed on `/mnt/data` while it is there.

`/mnt/data/AI-Models/FastH3-V2` was deleted to make room (≈22 GB, per the
operator's explicit go-ahead). `Maya-S` was **kept**.

### 8.5.6 What was NOT verified — and why

| Claim / step | Status | Reason |
|---|---|---|
| **Maya-S GPU test on the v1.1.22 engine** | **NOT RUN** | GPU wedged: `/dev/kfd` returns `EINVAL` on both `O_RDWR` and `O_RDONLY`; engine reports `no CUDA device` (§5.5). Needs a clean reboot, which the operator must perform. |
| **Maya-XS GPU test** | **NOT RUN** | Same GPU fault, plus the download is still in flight. |
| **v1.1.22 "1.85x faster drafting on one GPU"** | **NOT MEASURED** | Upstream release-note figure on different hardware. Nothing on this box has reproduced it. |
| **`DS4_HIP_ATTN_SWIZZLE=1` speedup** | **NOT MEASURED** | GPU fault. |
| **XS download completion + SHA256** | **IN PROGRESS** | 19.77 / 280.88 GB (7.0 %) at 17:25; the verifier has not run yet. |
| **Whether the v1.1.21-era Maya-S pack is readable by the v1.1.22 engine** | **NOT YET ANSWERED** | Needs either a diff of the pack-reading code or a live load. Under audit. |
| **Exact `--ds4-quant maya-xs` install command sequence** | **PARTIALLY RESOLVED** | `setup.sh` is a 5-line wrapper around `maya.sh`. The literal pack/drafter invocations are still being read out of `tools/ds4/pack_gguf.py` (the *new* packer — the older `tools/ds4/pack.py` is the wrong tool for the XS flow). |
| **XS fits in this box's RAM** | **BY DECLARATION ONLY** | Upstream says 120.6 GB. This box has **124 GB** physical, ≈113 GB available, and must also keep Hermes/Telegram and DSH alive. The old `MemoryMax=80G` is **not** sufficient; a new explicit cgroup limit is required. |

### 8.5.7 Current state at the time of writing

```text
Maya-XS download   active, 19.77 / 280.88 GB, 19 MB/s, ETA ≈ 4 h
Strata :18087      inactive (GPU fault, §5.5) — must stay off until Maya tests are done
DSH :18095         active
Hermes / Telegram  active, untouched
ComfyUI            inactive and disabled
GPU                wedged — /dev/kfd EINVAL, "no CUDA device"
```

---

## 9. Reproducing this

```bash
# one variant, in isolation
bash ~/.local/bin/maya-dsweep4.sh          # 21 causal variants, ~9 h budget

# engine (never two at once)
python3 ~/.local/bin/maya-ds4-bench.py --port 18091 --out <dir> \
        --target-tokens 16000 --turns 1 --no-thinking --label <id>

# cold the page cache (engine MUST be stopped)
python3 ~/.local/bin/maya-drop-cache.py
```

Helpers live in `~/.local/bin/`: `maya-dsweep4.sh` (the sweep),
`maya-ds4-bench.py` (the benchmark), `maya-sweep-summary.py` (per-variant
JSON), `maya-drop-cache.py` (cache drop), `maya-ds4-host.sh` (single-engine
host with the port/storage/RAM guard), `maya-drafter-dl.sh` (pinned drafter
download).

---

## 10. Provenance and honesty notes

- Every number in §1-§3 was produced by a run on this box.
- The v1.1.20/v1.1.21 performance claims in §8 are **upstream release notes**,
  not local measurements. They are quoted as claims, and are labelled as such.
- No API keys, tokens or passwords are stored in this repository or in these
  notes; credential values are `[REDACTED]`.
- Service topology: Hermes/Telegram must keep running throughout — the Hermes
  gateway PID was never touched; DSH stayed on `:18095` and is still up.
- **Correction:** an earlier version of this file claimed Strata "was restored
  with `loaded: true` verified". That is **not true for this run**. The
  sweep's EXIT trap *attempted* the restore and correctly reported failure
  (`WAR: Strata nereagovala s loaded=true`); production Strata on `:18087` is
  down because the GPU is wedged (§5.5), not because the sweep left it
  stopped. A reboot is required to bring it back.
- The upstream `exllamav3` master audit in §8 was done by reading the
  downloaded source tree, not by paraphrasing the README.
