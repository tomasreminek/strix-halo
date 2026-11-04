# Talus 0.1.3 + Strata vision front-end — the production config (2026-11-04)

Marker: `TALUS_VISION_20261104`

This is the exact configuration running on Hilbert right now: **Talus** as the inference engine
(fast prefill, MTP draft head) behind **Strata's Python `serve.server`** front-end, which adds the
vision/OCR path that `talus-server` 0.1.3 lacks.

Measured decode with this config: **49.8 / 56.4 / 48.3 / 61.5 tok/s** at 2k / 8k / 32k / 66k
(prefill 1 058 / 1 346 / 1 385 / 1 350 tok/s). Vision adds ~0 cost to the text path.

---

## Why two layers

`talus-server` (the Rust HTTP server shipped with Talus 0.1.3) has **no image input**: an
`image_url` part returns

```json
{"message": "image input is not supported by this model", "code": "unsupported_content"}
```

The Talus *engine* itself understands the GENI vision protocol (`talus-cli --vision`), but the
bundled server never sends it. Strata's `serve.server` (Python) does: it runs `strata-vision-hip`
on the mmproj, prepends the image embeddings, and forwards to the engine over GENI. So the working
combination is:

```
OpenAI client -> serve.server (Python, :18087) -> talus-cli --vision --serve (engine, GENI)
                        |
                        +-> strata-vision-hip (mmproj -> image embeddings)
```

`serve.server` speaks `/v1/chat/completions` exactly like before, so clients (Hermes, DSH) need no
change — same model id, same port, same 131 072-token context, still 2 slots.

## Files

- `run-vision.json` — engine + vision config handed to `serve.server --config`
- `talus-vision-server.sh` — launcher (`cd` into the control component, set the ROCm/STRATA env, exec)
- `talus-qwen.service` — systemd user unit that runs the launcher
- `bench_talus-vision-final.json` — raw benchmark rows from this config

Paths in `run-vision.json` are absolute to this box. Adjust the five locations
(pack, native GGUF, expert-profile, mtp rt dir, draft vocab) plus the `vision.exe` / `vision.mmproj`
pair, then it runs anywhere the Talus 0.1.3 gfx1151 build runs.

## Engine arguments

```
--pack            ~/Projekty/Strata-data/packs/unsloth-ud-iq4_xs
--native          .../Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf
--expert-profile  <talus dist>/data/expert-profile.bin
--expert-cache    17714
--prefill         auto
--spec 4 --spec-min-p 0.5
--max-context     131072
--kv int8 --ple-io ram --kv-resident 32768
--resident-budget-gib 55 --vram-reserve-mib 700
--batch           2
--mtp             ~/Projekty/Strata-data/mtp-bf16/rt
--mtp-window      8192
--mtp-draft-vocab <talus dist>/data/draft_vocab_en.bin
--vision
--serve
```

Environment (the ROCm SDK is TheRock, installed outside the distro):

```
PYTHONPATH=/mnt/c/ai/rocm-sdk
STRATA_PF_FUSED=1 STRATA_PF_GEMM=1 STRATA_HC_UPMIX=1 STRATA_PA_FAST=1
STRATA_HIP_WMMA=1 STRATA_SELECT_WMMA=1 STRATA_HC_Q8=1
STRATA_PF_SWITCH_MIN_T=0 STRATA_PREFILL_STREAM_MIN=128
```

## Launcher

```bash
#!/usr/bin/env bash
set -euo pipefail
CONTROL="$HOME/.local/share/strata/components/control/0.1.56"
cd "$CONTROL"                       # serve is a module inside the control component
exec env PYTHONPATH=/mnt/c/ai/rocm-sdk \
  STRATA_PF_FUSED=1 STRATA_PF_GEMM=1 STRATA_HC_UPMIX=1 STRATA_PA_FAST=1 \
  STRATA_HIP_WMMA=1 STRATA_SELECT_WMMA=1 STRATA_HC_Q8=1 \
  STRATA_PF_SWITCH_MIN_T=0 STRATA_PREFILL_STREAM_MIN=128 \
  "$CONTROL/python/bin/python3.12" -m serve.server \
    --engine strata \
    --config "$HOME/.config/talus/run-vision.json" \
    --host 127.0.0.1 --port 18087
```

**Pitfall:** `cd` into the control component is mandatory. Without it the launcher dies with
`ModuleNotFoundError: No module named 'serve'` and systemd restart-loops.

## systemd unit

```ini
[Unit]
Description=Talus engine (Qwen3.8-Flash-Next, 2 slots, MTP) behind Strata serve.server — vision/OCR on :18087

[Service]
Type=simple
ExecStart=%h/.local/bin/talus-vision-server.sh
Restart=on-failure
RestartSec=20
TimeoutStartSec=infinity
MemoryMax=110G
KillMode=control-group     # serve.server spawns the engine; take both down together
KillSignal=SIGTERM
TimeoutStopSec=45

[Install]
WantedBy=default.target
```

Cold start to `{"status": "loaded"}` is **~48 s** (expert cache fill). `MemoryMax=110G` matters:
the engine holds ~55 GiB of resident expert cache plus the 807 MiB MTP draft layer.

## Measured (2026-11-04, this exact config)

Method: cold prefill with a fresh random salt in the prompt (otherwise the calibration probes warm
the prefix cache and prefill looks ~100× faster than reality), then 256 warm decode tokens.

| depth | prefill tok/s | decode tok/s |
|---|---:|---:|
| ~2 000 | 1 058 | 49.8 |
| ~8 000 | 1 346 | 56.4 |
| ~31 800 | 1 385 | 48.3 |
| ~65 700 | 1 350 | 61.5 |
| ~126 600 | 1 271 | 42.9 |

The 128k point needs the coding worker stopped. Two concurrent slots on one GPU make decode
meaningless — a run with the worker active reported 1.45 tok/s, which is contention, not the
engine. With the worker down and only slot 0 busy: **1 270.8 tok/s prefill (99.62 s for 126 600
tokens) and 42.86 tok/s decode over 256 tokens, warm TTFT 171 ms**. Full record and method in
`docs/talus-128k-context-20261104.md`.

For comparison on the same weights and the same box:

- **Strata 0.1.56** (previous production): prefill 564 / 781 / 750 / 714, decode 32.2 / 36.9 / 37.2 / 56.5
- **Talus 0.1.3, no MTP**: prefill 1 049 / 1 372 / 1 400 / 1 363, decode 37.3 / 40.0 / 36.8 / 60.6

So: prefill ~1.8–1.9× faster than Strata, and MTP lifts decode from a tie into a clear win.
Prefill is unchanged by MTP and by the vision front-end — it is the same engine path.

## Vision / OCR

Test image: a page of the Krusičany stable-cadastre overview (`prehled_om3336.jpg`), 1 026 prompt
tokens including the image, 571 completion tokens, **10.8 s end to end (~52.9 tok/s)**.

It transcribed the actual map labels — `KRUSCHAN`, `KRUSYAN`, `BRNATITZ`, `OBRAHOFAN`,
`Haus Dinnowitz, Glöckelwitz, Schöna-Twinitz im Böhmischem Truppenkreis 1836`, plus the sheet ids
`22759-02_a_AC_1136_1` … `22759-02_j_AC_1136_6`.

**Critical for OCR quality:** send `chat_template_kwargs: {"enable_thinking": false}`. This model is
a reasoning model; with thinking on it spends the entire `max_tokens` budget inside
`reasoning_content` and `content` comes back empty. With thinking off the transcription is direct.

```bash
curl -s http://127.0.0.1:18087/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "qwen3.8-flash-next-unsloth-ud-iq4_xs", "max_tokens": 1400, "temperature": 0,
  "chat_template_kwargs": {"enable_thinking": false},
  "messages": [{"role": "user", "content": [
    {"type": "text", "text": "Vypiš pouze text, který vidíš na skenu."},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}]}]}'
```

## Reproduce from scratch

1. Install Talus 0.1.3 prebuilt for gfx1151 (`talus-v0.1.3-linux-x86_64-gfx1151.tar.gz`) — binaries
   `talus-cli`, `talus-server`, `tools/mtp_*.py`, `data/{expert-profile.bin,draft_vocab_en.bin}`.
2. ROCm SDK (TheRock `10.2.0a20261014`, gfx1151) into `/mnt/c/ai/rocm-sdk`; export `PYTHONPATH`.
3. Build the MTP head from the stock BF16 checkpoint (see `docs/talus-v013-vs-strata-20261104.md`):
   `mtp_fetch.py` → `mtp_pack.py --experts q2_0` → `mtp_rt.py`. Needs a `gguf-py` with
   `GGMLQuantizationType.Q2_0` (`STRATA_GGUF_PY`).
4. Have a Strata `control` component installed (0.1.56 here) — it provides `serve.server`,
   its bundled python 3.12, and the matching `engine/…/strata-vision-hip` + `mmproj` pair.
5. Drop `run-vision.json` into `~/.config/talus/`, fix the absolute paths, install the launcher and
   the unit, `systemctl --user daemon-reload && systemctl --user enable --now talus-qwen.service`.
6. Verify: `curl -s localhost:18087/v1/models` → `{"status": {"value": "loaded"}, "meta": {"n_ctx": 131072}}`,
   then run the OCR curl above.

## Caveats

- **The MTP draft head comes from the stock Qwen BF16 checkpoint**, while the served weights are the
  Huihui-abliterated Unsloth UD-IQ4_XS. Draft acceptance is therefore approximate. The tok/s numbers
  are measured; the head/weight pairing is not ideal.
- Talus and Strata cannot both hold the model — it is one engine at a time on this box.
- `serve.server` is the front-end only; all the throughput comes from the Talus engine underneath.
