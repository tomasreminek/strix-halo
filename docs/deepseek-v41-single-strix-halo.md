# DeepSeek V4.1 on a single Strix Halo — reproduction and coding verdict

**2026-09-17 · Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124 GiB visible unified memory, Pop!_OS / Linux 7.0.11.**

Marker: `DEEPSEEK_V41_COMMUNITY_20260917`.

## Bottom line

It runs, using SSD-streamed experts. It was not a practical winner on this machine. **I stopped the overnight optimization experiment.** No replicated useful acceleration emerged from the second pass. Small coding and Czech tests worked, but the real Tapper game trial failed acceptance: the first complete game had broken service/return mechanics, and I found the delivered repair unplayable on mobile. A further DeepSeek-authored mobile repair was requested separately; it is not an accepted result of the overnight trial.

The exact tested model is **DeepSeek V4.1 Flash Q2**, not another DeepSeek version and not a higher-quality quant. This result is about this checkpoint/runtime/hardware combination, not a general model-quality ranking.

- [Overnight measurements and full experiment matrix](deepseek-v41-night-20260917.md)
- [Second-pass acceleration attempts and pressure failures](deepseek-v41-speed2-20260917.md)
- [Current model comparison](model-comparison.md)

## Measurements worth keeping

Three fresh-server cache80 repetitions gave median full-request times of **29.21 s for Python**, **26.41 s for a bugfix**, **20.41 s for Czech**, **11.49 s for tool-shaped JSON**, and **8.42 s for extraction**. Small sandbox tests passed; strict only-code formatting sometimes failed. Tool-shaped JSON is not proof of native tool-call support.

The largest finalist median completion-token/full-request rate was **7.12 tokens/s**, including reasoning. **That is not native decode speed**, and that request took 42.69 s, with the first useful answer at 37.65 s. Natural page-cache history, fixed suite order, and unmatched alternatives prevent a causal universal speed claim.

Actual populated-context runs reached **7,157 / 31,679 / 64,461 prompt tokens**, generating 622 / 564 / 556 output tokens in **149.28 / 370.60 / 687.38 seconds**. Retrieval and sandbox code passed; requested word counts failed. **128k remained inconclusive** after a 905.52 s calibration timeout without a final answer. Allocating a 128k slot is not passing a real 128k test.

The second pass found no replicated acceleration. Larger-cache attempts pressure-aborted; read-worker changes did not show a gain; mapped-memory GPU microtests did not translate into completed faster inference. MTP/DSpark was unsupported for this exact V4.1 path. **Cache24 was the lower-residency fallback used for Tapper, not a faster configuration.** Its single Python/Czech observations were 33.32 / 32.19 s.

## Real coding trial: DeepSeek itself wrote Tapper

Task: a procedural Three.js Tapper-inspired game in one HTML file, with keyboard and mobile touch controls. The controller supplied requirements and defect feedback, extracted the HTML, and embedded Three.js; **gameplay and repair code came from local DeepSeek**, not a substitute model.

| Attempt | Output tokens | HTTP wall | TTFT | Outcome |
|---|---:|---:|---:|---|
| generate01 | 6,200 | 1,458.93 s | 27.23 s | Output limit reached; incomplete HTML |
| generate02 | 4,637 | 1,101.89 s | 43.21 s | Complete HTML; real desktop/mobile-emulated QA rejected core service/return loop |
| repair03 | 4,479 | 1,143.86 s | 29.16 s | Complete repair; owner rejected as unplayable on his physical phone |
| repair04 | 5,259 | 1,274.18 s | — | Complete targeted mobile rework (camera aspect, control layout, per-object meshes). **Also unusable on the real phone; experiment stopped, no accepted mobile build.** |

Total through repair04: **20,575 output tokens and 4,978.86 s (83 min) of model-request wall time**, ~3.9–4.2 end-to-end (non-decode) tok/s. No gameplay passed acceptance; the owner stopped the experiment. generate02 and repair03 achieved **4.21 and 3.92 completion tokens/s end-to-end**, respectively, not certified native decode. Failed attempts remain in the accounting.

Raw requests, complete responses, stream timestamps and native logs are retained locally under `benchmarks/qwen38-acceleration/runs/deepseek-v41-tapper-20260917/`. [Public compact measurement ledger](../records/benchmarks/deepseek-v41-tapper-20260917/measurements.json) records actual usage and timings without private environment dumps.

A later QA environment could not create a WebGL context. That is a **test-environment blocker**, not evidence that gameplay passed or the cause of the owner's phone experience. Mobile emulation is not physical-phone testing. The requested fourth repair is a separate follow-up; no successful mobile fix is claimed here.

## Reproduce the exact baseline

### 1. Requirements and disk budget

Use a Linux ROCm setup that really supports `gfx1151`, a **complete ROCm 7.2.4 development SDK** (including HIP headers and hipBLAS development libraries), Git, make, a C/C++ toolchain with complete headers, and Python. This host needed GCC 13 explicitly because an installed newer GCC lacked its C++ headers. Do not copy NVIDIA or a different AMD architecture's recipe unchanged.

The checkpoint is **365,713,686,528 bytes (about 340.6 GiB)**. Reserve that plus download/cache overhead and a safety margin on the **target filesystem**. A single SSD-streamed checkpoint must fit on that volume; unrelated free space elsewhere does not help. A ZHITAI TiPlus7100s NVMe negotiated PCIe 4 x4 here. This experiment does not prove an SSD upgrade will solve the bottleneck.

Stop competing GPU workloads before loading. Do not use `swapoff`, drop caches, change global THP, or weaken memory guards to force a result. The 80 GiB cache is **historical measurement only**: subsequent pressure failures disqualify it as a blanket recommendation. Start with the measured lower-residency **24GB** setting and monitor host available RAM, swap/pageout and memory pressure as well as process RSS (GPU/GTT allocations are not fully represented by RSS).

### 2. Pinned model download and checksum

Review the model license/card: <https://huggingface.co/antirez/deepseek-v4.1-flash-gguf>.

```bash
python3 -m venv "$HOME/.venvs/deepseek-download"
"$HOME/.venvs/deepseek-download/bin/pip" install huggingface_hub
export MODEL_DIR="$HOME/models/deepseek-v4.1-flash-q2"
mkdir -p "$MODEL_DIR"
"$HOME/.venvs/deepseek-download/bin/hf" download \
  antirez/deepseek-v4.1-flash-gguf DeepSeek-V4.1-Flash-Q2.gguf \
  --revision dd8a266f7145edc19e2334b46e19b6821f221dc7 \
  --local-dir "$MODEL_DIR"
export MODEL="$MODEL_DIR/DeepSeek-V4.1-Flash-Q2.gguf"
stat -c '%s' "$MODEL"
sha256sum "$MODEL"
```

Required size: `365713686528`. Required SHA-256:

```text
1ce6a8f8806205c13330d7ca287bd198331dc5ca35ccc5d8a9a92a188a6f6f42
```

Do not proceed on a mismatch or an unfinished download.

### 3. Pinned ROCm source and the required host fix

```bash
git clone https://github.com/tomasreminek/strix-halo.git "$HOME/strix-halo-recipes"
git clone https://github.com/kyuz0/ds4.git "$HOME/ds4-v41"
cd "$HOME/ds4-v41"
git checkout --detach 09f12d415bb42efc1887e9330b0aebe9c32902da
git apply --check "$HOME/strix-halo-recipes/recipes/deepseek-v41/host-sqrt.patch"
git apply "$HOME/strix-halo-recipes/recipes/deepseek-v41/host-sqrt.patch"
```

This patch changes one host-side attention scalar from device-only `rsqrtf` to `1.0f / sqrtf`. The local tested patched commit was `869a09dec445def450bf2d7e6333ced5b9152753`; **it is a local commit, not a promise that upstream can fetch that SHA**. The public patch plus pinned parent reproduces its source change. This is a portability fix, not an acceleration claim.

On a complete conventional ROCm 7.2.4 installation:

```bash
export ROCM_PATH=/opt/rocm-7.2.4   # set to your complete SDK root
export HIP_PATH="$ROCM_PATH"
export PATH="$ROCM_PATH/bin:$PATH"
export LD_LIBRARY_PATH="$ROCM_PATH/lib:$ROCM_PATH/lib64:${LD_LIBRARY_PATH:-}"
"$ROCM_PATH/bin/hipcc" --version
make strix-halo ROCM_ARCH=gfx1151 \
  HIPCC="$ROCM_PATH/bin/hipcc --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13" -j2
./ds4-server --help
```

**Portability boundary:** the command above substitutes a complete SDK for this host's split non-system SDK; it has not been rebuilt on every distribution. Use your actual complete GCC installation or omit the GCC override where automatic selection is valid. The exact locally executed build used:

```bash
ROCM=/mnt/data/rocm-724-prefix/opt/rocm-7.2.4
OUT=/home/tomasreminek/benchmarks/qwen38-acceleration/runs/deepseek-v41-night-20260916
make strix-halo ROCM_ARCH=gfx1151 \
  HIPCC="$ROCM/bin/hipcc --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -I$OUT/build-deps/root/opt/rocm-7.2.4/include -L$OUT/build-deps/link -L$ROCM/lib" -j2
```

Those extra include/link paths supplied missing SDK development components locally. They are **not downloadable prerequisites hidden in this repository**. If your build reports missing headers/libraries, install the corresponding development components for the same ROCm version rather than mixing versions. A successful build/help invocation is not a successful model inference test.

### 4. Run the lower-residency configuration

In the build shell with the environment above, after confirming that no competing model/render owns the GPU:

```bash
./ds4-server --rocm -m "$MODEL" \
  --ssd-streaming --ssd-streaming-cache-experts 24GB \
  --ctx 8192 --batched-session 1 \
  --host 127.0.0.1 --port 18095
```

The local guarded runner used a dedicated systemd user unit, `MemoryMax=56G`, `MemorySwapMax=1G`, `RuntimeMaxSec=1950` for coding, plus stricter telemetry-based early aborts and a shared GPU lock. These cgroup limits **do not bound all ROCm driver memory**. Keep at least 12 GiB available as a hard abort floor; the tested short-context cache24 runtime planned about 35.09 GiB including static buffers and reserves. A plan is not measured peak usage.

### 5. Verify readiness and make a real request

From another terminal:

```bash
curl --fail http://127.0.0.1:18095/v1/models
curl --fail --max-time 180 http://127.0.0.1:18095/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-v4.1-flash","messages":[{"role":"user","content":"Write a Python function returning the first index of a value in a list, or -1 if absent. Code only."}],"temperature":0,"reasoning_effort":"none","max_tokens":256,"stream":false}'
```

`/health` is not the correct readiness endpoint in this pinned ds4 runtime. A model-list response proves startup only; inspect the generated answer and execute code in an appropriate sandbox. Do not expose this unauthenticated local server publicly. Stop the owned server after testing; preserve weights and evidence.

## What I recommend instead

**Qwen3.8 Flash-Next, native Halogen 0.11.0 quality overlay with MTP**, remains my speed-first choice on this box: **44.66 tok/s short**, **40.08 at real ~64k**, **38.03 at real ~126k**, using 256 generated tokens. Practical Czech/coding/tools/JSON/Responses/vision checks passed. The serial-versus-MTP byte-identity gate failed and still needs review; the engine is closed source. [Exact recipe and caveats](qwen38-halogen.md).

I also tested **GLM-5.3-Flash AJ-IQ2_XXS**, 81.35 GiB, on Unsloth MIX ROCm gfx1151: **14.63 tok/s server decode**, versus **8.57 on Vulkan** for the same quant. A 128k KV allocation / 64k configured agent window must not be confused with Qwen's actually filled-context benchmark. [GLM recipe](glm-53-flash.md).

These are different checkpoints, quantizations and workloads. DeepSeek's request-wall rates cannot be turned into a clean speed ratio against native decode measurements.
