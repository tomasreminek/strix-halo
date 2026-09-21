# K2 Horizon candidate sweep · 2026-09-21

Hardware: Hilbert, AMD Ryzen AI MAX+ 395 / Radeon 8060S `gfx1151`, Pop!_OS Linux 7.0.11, 124 GiB unified memory.

Runtime used for GGUF loader attempts: `/mnt/data/bonsai-demo/bin-rocm/llama-server`, version `0.2.0-dev`, build `10683`, commit `d8f26eec7`, ROCm libraries `/mnt/data/rocm-724-prefix/opt/rocm-7.2.4`.

Policy: candidates were tested serially on an idle GPU. No candidate was made the Hermes/Telegram default. The production route remained `openai-codex / gpt-5.6-sol`.

## Summary

| Candidate | Artifact | Result | Gate |
|---|---|---|---|
| `darkc0de/K2-Horizon-3.7B-heretic-xortron` | Transformers/Safetensors, 3 shards | **BLOCKED** | No GGUF; requires custom Transformers/K2 runtime |
| `geantendormi/K2-Horizon-7B-Uno-Uncensored-GGUF` | `K2-Horizon-7B-Uno-Uncensored-IQ4_XS.gguf` | **BLOCKED** | llama.cpp: `unknown model architecture: 'k2-horizon'` |
| `kingjones777/K2-Horizon-7B-ROCmFP4-GGUF` | `K2-Horizon-7B-Q4_0_ROCMFP4_STRIX_LEAN.gguf` | **BLOCKED** | GGUF tensor type 100 unsupported by this loader |

## 1. darkc0de K2 Horizon 3.7B heretic xortron

Source: https://huggingface.co/darkc0de/K2-Horizon-3.7B-heretic-xortron

Hub inventory showed three Safetensors shards:

- `model-00001-of-00003.safetensors` — 4,978,244,368 B
- `model-00002-of-00003.safetensors` — 4,981,006,808 B
- `model-00003-of-00003.safetensors` — 157,297,568 B

The repository also contains custom `configuration_k2_horizon.py` and `modeling_k2_horizon.py`. It contains no `.gguf` artifact. This was therefore a preflight **BLOCKED** result for the pinned local llama.cpp/ROCm test path; the large Safetensors checkpoint was not downloaded or converted speculatively.

## 2. geantendormi K2 Horizon 7B Uno Uncensored

Source: https://huggingface.co/geantendormi/K2-Horizon-7B-Uno-Uncensored-GGUF

Artifact: `K2-Horizon-7B-Uno-Uncensored-IQ4_XS.gguf`

- Size: 5,113,641,824 B
- SHA-256: `fe004f0022a88d2c13f3c03c126922d1d7d4f27ae915b2b2e67a8f33bf1519ad`

Loader command:

```bash
env LD_LIBRARY_PATH=/mnt/data/bonsai-demo/bin-rocm:/mnt/data/rocm-724-prefix/opt/rocm-7.2.4/lib \
  /mnt/data/bonsai-demo/bin-rocm/llama-server \
  -m /mnt/data/models/k2-horizon-7b-uno/K2-Horizon-7B-Uno-Uncensored-IQ4_XS.gguf \
  --port 18083 --host 127.0.0.1 \
  -a k2-horizon-7b-uno-iq4xs -ngl 99 -c 32768 --jinja \
  --reasoning off --reasoning-format deepseek --reasoning-budget 0
```

Observed loader failure:

```text
E llama_model_load: error loading model: unknown model architecture: 'k2-horizon'
E llama_model_load_from_file_impl: failed to load model
E srv load_model: failed to load model
E llama_server: exiting due to model loading error
```

Verdict: **BLOCKED** at model initialization. No API, context, speed, or Hermes test was run.

## 3. kingjones777 K2 Horizon 7B ROCmFP4

Source: https://huggingface.co/kingjones777/K2-Horizon-7B-ROCmFP4-GGUF

Selected the hardware-specific `STRIX_LEAN` artifact:

- File: `K2-Horizon-7B-Q4_0_ROCMFP4_STRIX_LEAN.gguf`
- Size: 5,259,885,696 B
- SHA-256: `f93ca7e2c55235e8fbe665b63d6fdba3cfeb33be7e046335d4934db1bda87d37`

Observed loader failure:

```text
E common_fit_params: encountered an error while trying to fit params to free device memory: failed to load model
E gguf_init_from_reader: tensor 'blk.0.attn_k.weight' of type 100 ((null)) has 4096 elements per row, not a multiple of block size (0)
E gguf_init_from_reader: failed to read tensor info
E llama_model_load: error loading model: llama_model_loader: failed to load model
E llama_server: exiting due to model loading error
```

Verdict: **BLOCKED** at GGUF tensor parsing. This is a runtime/tensor-format compatibility failure, not an inference-quality or speed result. No Hermes route was changed.

## Related tested local candidates

### MiniCPM5 abliterated Q8_0

`mradermacher/abliterated-minicpm5-2b-v3-GGUF`, `abliterated-minicpm5-2b-v3.Q8_0.gguf`, 2,679,711,744 B, SHA-256 `4a50bf3a40751420d0511a44023485ab7e1ce812dd96d9b7434f67642496eb10`.

- Loader and API startup: **PASS**
- Short deterministic direct API response: **PASS**
- Direct OpenAI tool-call request: **PASS** (`get_weather(city="Prague")`)
- ~70k-token marker retrieval: **FAIL**
- Full Hermes agent short-response test: **FAIL**; garbled runaway output, approximately 17k generated tokens before cancellation
- Final verdict: **REJECTED as Hermes main model**; weights retained for possible isolated runtime/template work

### Bonsai 2 27B Uncensored

Bonsai loaded and answered a minimal direct API request, but Hermes tool-calling triggered `Unexpected empty grammar stack after accepting piece`. It was removed from the machine and from Hermes configuration after the failed agent gate. It is not a production candidate.

## Decision

No K2 Horizon candidate passed the loader gate on the current ROCm/llama.cpp build. Do not promote any of the three candidates to Hermes or Telegram. A future test requires either a llama.cpp build with native `k2-horizon` support and tensor type 100 support, or the model vendor's supported runtime; that would be a separate compatibility experiment, not evidence for the current production route.
