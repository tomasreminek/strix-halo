# Overall winner: native Halogen Qwen3.8 Flash-Next

**Measured 2026-09-16 on AMD Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124 GiB visible unified memory.**

This is the current **overall performance winner** and the recommended main-model direction. It outranks the uncensored Orca route because speed is the primary decision criterion.

- **Overall / aligned winner:** native Halogen Qwen3.8 Flash-Next, default quality overlay.
- **Uncensored fallback:** OrcaRouter Q4_K_M + EasiiX Q8_0 MTP on Nathanw v0.7.6.
- **Halogen + OrcaRouter IQ4_XS:** loader-blocked, not benchmarked. Its dense trunk contains `Q5_K`; Halogen requires dense `Q8_0`.

## Measured result

The serving rows below used MTP, 256 generated tokens and a 131,072-token server slot. The long-context prompts were actually filled; merely configuring a 128k slot does not count.

| depth | MTP decode mean | min–max | commit / round |
|---|---:|---:|---:|
| short serving set | **44.66 tok/s** | 38.13–51.94 | 1.70 |
| ~32k prompt | **41.37 tok/s** | 35.44–48.95 | 1.67 |
| ~64k prompt | **40.08 tok/s** | 32.97–46.46 | 1.64 |
| ~126k prompt | **38.03 tok/s** | 31.57–44.95 | 1.63 |

The practical quality/API gate passed:

- Czech with diacritics;
- Python parsed and executed against tests;
- OpenAI tool call;
- strict JSON schema;
- OpenAI Responses API;
- vision OCR (`ORBIT 4729`).

### Transparent caveat

The upstream serving benchmark also compares serial greedy output against MTP output byte for byte. That identity gate failed in every completed serving regime, although the practical quality/API checks passed. Therefore the exact status is:

```text
COMPLETE_PERFORMANCE_GATE_PASSED_IDENTITY_REVIEW_REQUIRED
```

Speed is the primary selection criterion here, so Halogen is listed as the winner. The identity mismatch remains published evidence, not hidden or reclassified as a pass.

## Components and pinned provenance

### Engine

- Repository: <https://github.com/peonist-ai/halogen-flash-server>
- Container: `ghcr.io/peonist-ai/halogen-flash-server:0.11.0`
- Locally verified Docker image ID: `sha256:7f4036110c6b316d72c3bc534bd5cd88af3078ca1d59fe710f3e342a534d3598`
- The engine is closed source and has separate terms. Review the server repository before deployment.

### Native checkpoint

- Repository: <https://huggingface.co/peonist-ai/halogen-qwen3.8-flash-next>
- Pinned revision used for the measured matrix: `b8dbb46d03f5d1d0e63b432c2ca763db7e8e0aa4`
- Base model: `Qwen/Qwen3.8-Flash-Next`
- Format: native `.hgn`; not compatible with llama.cpp, Transformers or vLLM

Required quality-profile files:

```text
9c116bbc01f77b7a15464c1a124eb3325b286089b8a2a6f2856c9b246a235bd6  qwen38-flash-next-w4b.hgn          124,068,083,904 B
1cdfc3a9f988955bfe9a71bb808d393030abbf9f99d34ffa1ef93815a49b39ab  qwen38-flash-next-w4b.overlay.hgn    2,572,466,560 B
```

Optional files used by this validation:

```text
d62e0ae553fe88afd3833733d4a4c669f34d20fd8dfce4b9610525bed2134b10  qwen38-flash-next-vision.hgn          897,916,416 B
```

Other published optional files, not needed for the winning native-quality command:

```text
f49c8d14fa972c1db5115c714981e399585a6a98106a1a055d9e77026bb6de4c  qwen38-flash-next-w4b.overlay-speed.hgn  2,478,095,488 B
0f50e9626df98168e7c6e0cc264e2a92b5184dd885a175a06628d979b5edceeb  qwen38-flash-next-mtp.hgn                1,523,566,720 B
```

The native checkpoint already carries its MTP head. `qwen38-flash-next-mtp.hgn` is required only when loading a compatible third-party GGUF.

## Exact download

Use a virtual environment because modern distributions may enforce PEP 668:

```bash
python3 -m venv "$HOME/.venvs/hf"
"$HOME/.venvs/hf/bin/pip" install -U 'huggingface_hub[cli]'

MODEL_DIR="$HOME/models/halogen-qwen38-flash-next"
"$HOME/.venvs/hf/bin/hf" download \
  peonist-ai/halogen-qwen3.8-flash-next \
  qwen38-flash-next-w4b.hgn \
  qwen38-flash-next-w4b.overlay.hgn \
  qwen38-flash-next-vision.hgn \
  README.md \
  tokenizer/chat_template.jinja \
  tokenizer/generation_config.json \
  tokenizer/merges.txt \
  tokenizer/tokenizer.json \
  tokenizer/tokenizer_config.json \
  tokenizer/vocab.json \
  --revision b8dbb46d03f5d1d0e63b432c2ca763db7e8e0aa4 \
  --local-dir "$MODEL_DIR"
```

Verify the large files before loading:

```bash
cd "$MODEL_DIR"
printf '%s  %s\n' \
  9c116bbc01f77b7a15464c1a124eb3325b286089b8a2a6f2856c9b246a235bd6 qwen38-flash-next-w4b.hgn \
  1cdfc3a9f988955bfe9a71bb808d393030abbf9f99d34ffa1ef93815a49b39ab qwen38-flash-next-w4b.overlay.hgn \
  d62e0ae553fe88afd3833733d4a4c669f34d20fd8dfce4b9610525bed2134b10 qwen38-flash-next-vision.hgn \
  | sha256sum -c -
```

## Pull and verify the measured container

```bash
docker pull ghcr.io/peonist-ai/halogen-flash-server:0.11.0

docker image inspect ghcr.io/peonist-ai/halogen-flash-server:0.11.0 \
  --format '{{.Id}}'
# measured image ID:
# sha256:7f4036110c6b316d72c3bc534bd5cd88af3078ca1d59fe710f3e342a534d3598
```

A registry tag can move. If the image ID differs, record it and treat the run as a new runtime revision rather than silently calling it the measured configuration.

## Exact winning server command

Resolve the host device groups numerically. Container images may not define host group names such as `render`.

```bash
MODEL_DIR="$HOME/models/halogen-qwen38-flash-next"
VIDEO_GID="$(getent group video | cut -d: -f3)"
RENDER_GID="$(getent group render | cut -d: -f3)"

docker run --rm --name halogen-qwen38 \
  -p 127.0.0.1:8731:8731 \
  --device /dev/kfd --device /dev/dri \
  --group-add "$VIDEO_GID" --group-add "$RENDER_GID" \
  --ipc=host --ulimit memlock=-1:-1 \
  -e HALOGEN_CTX=131072 \
  -e HALOGEN_KV_POOL_POSITIONS=131072 \
  -e HALOGEN_KV_SLOTS=1 \
  -e HALOGEN_MAX_TOK=32768 \
  -e HALOGEN_PROMPT_CACHE=2 \
  -e HALOGEN_VISION_TOWER=1 \
  -e HALOGEN_VERBOSE=1 \
  -v "$MODEL_DIR:/models:ro" \
  ghcr.io/peonist-ai/halogen-flash-server:0.11.0 all
```

Do **not** set `HALOGEN_CK_OVERLAY` for the winning quality profile. The adjacent `qwen38-flash-next-w4b.overlay.hgn` is selected automatically. Setting:

```bash
-e HALOGEN_CK_OVERLAY=/models/qwen38-flash-next-w4b.overlay-speed.hgn
```

selects the separate speed overlay, which measured slightly worse in this matrix at near-128k and is not the chosen winner.

Expect cold health readiness around two minutes. Keep other LLMs and GPU media workloads stopped; this is a one-heavy-workload configuration.

## API smoke

```bash
curl -fsS http://127.0.0.1:8731/health
curl -fsS http://127.0.0.1:8731/v1/models

curl -fsS http://127.0.0.1:8731/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model":"halogen-qwen3.8-flash-next",
    "messages":[{"role":"user","content":"Odpověz přesně: ČEŠTINA_OK"}],
    "max_completion_tokens":32,
    "temperature":0,
    "reasoning_effort":"none",
    "stream":false
  }'
```

Available endpoints include `/v1/chat/completions`, `/v1/completions`, `/v1/models` and `/v1/responses`.

## Why the uncensored Orca GGUF does not run in Halogen yet

The tested candidate was:

- <https://huggingface.co/orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF>
- revision `0434906af7b5202b676d43f108cf4f73d25691ef`
- `IQ4_XS`, three shards, `97,473,155,200 B`
- Halogen `0.11.1`, image ID `sha256:d1e860d26c578cf510f4ed85a60d1b69aa3f7e6708b5a62f3624cb35021df317`

Loader result:

```text
BLOCKED / INCOMPATIBLE_GGUF_TENSOR_LAYOUT
blk.0.attn_qkv.weight: Q5_K is not read by this engine
```

The filename describes the expert-oriented quant but does not guarantee a compatible dense trunk. Halogen currently accepts expert tensors such as `IQ4_NL`, `IQ4_XS`, `IQ3_S` or `Q4_0`, while the dense trunk must be `Q8_0`. The OrcaRouter artifact contains `Q5_K` in the dense attention tensor. No inference benchmark ran and this must not be reported as `0 tok/s`.

Until Halogen adds support or a compatible uncensored export appears, use the secondary uncensored route documented in [qwen38-flash-next.md](qwen38-flash-next.md): Orca Q4_K_M + EasiiX MTP on Nathanw v0.7.6.

## Evidence

- [`halogen-native-summary.json`](../records/benchmarks/qwen38-halogen-2026-09-16/halogen-native-summary.json)
- [`halogen-orcarouter-iq4xs-blocker.json`](../records/benchmarks/qwen38-halogen-2026-09-16/halogen-orcarouter-iq4xs-blocker.json)
- [`orca-nathanw-v075-v076-summary.json`](../records/benchmarks/qwen38-halogen-2026-09-16/orca-nathanw-v075-v076-summary.json)
- [`orca-nathanw-126k-sustained-summary.json`](../records/benchmarks/qwen38-halogen-2026-09-16/orca-nathanw-126k-sustained-summary.json)

Long-context source fixture SHA-256: `e4c3b195d68a870213e3180ff721df10b94ae162bbb7de6dc30b6c90f84ad4d5`.
