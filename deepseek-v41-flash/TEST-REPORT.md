# Strix Halo test report — DeepSeek V4.1 Flash

Date: 2026-09-14
Host: AMD Ryzen AI MAX+ 395 / Radeon 8060S / `gfx1151`

## Passed without model weights

- `python3 tools/test_budget.py` — PASS
- `python3 tools/test_engine_kwargs.py` — PASS
- `python3 tools/test_tune_draw.py` — PASS
- `python3 tools/test_atlas_export.py` — PASS (correctly reports no generated keep-set export)
- `python3 tools/test_tune_atlas.py` — PASS
- `python3 -m compileall -q engine tools server` — PASS
- `python3 tools/strix_halo_probe.py` — PASS as an audit; reports CUDA-specific upstream code

## Expected blocked gates

- `python3 server/test_server.py` — BLOCKED: no V4.1 tokenizer/checkpoint directory (`V41_MODEL_DIR` not set). This is intentional; the 510 GB checkpoint has not been downloaded.
- CUDA FP4/CB3 kernel tests — NOT RUN: they use `torch.cuda` and require the NVIDIA-specific kernel path.

## Static audit result

The copied upstream engine contains direct CUDA dependencies, including:

- 91 direct `torch.cuda` references in the scanned engine/tools/server/script trees
- 66 literal `"cuda"` device references
- 18 CUDA graph references
- 24 NVIDIA/`sm_121a`/GB10/CUDA-13 references

This confirms the next work is an AMD backend port, not a launcher/configuration change.

## Resource gate

No checkpoint was downloaded. No production model route, systemd unit, Hermes provider,
or Telegram default was changed.
