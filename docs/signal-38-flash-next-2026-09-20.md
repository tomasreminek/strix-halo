# Signal 3.8 Flash Next + Halogen external-GGUF tests

**Measured:** 2026-09-20 on AMD Strix Halo / Radeon 8060S (`gfx1151`), 124 GiB unified memory.

This record concerns the new **Signal 3.8 Flash Next** 177B MoE GGUF, not the older Signal 3.8 27B result elsewhere in this repository.

## Artifacts and integrity

Signal files were downloaded from `agentionai` and verified:

```text
427a7a10dd5a98d77c71be62a89d14e7408fc61a84c6efe889393852282cd3c6  Signal-3.8-Flash-Next-AP-Q4_K_XL.gguf
f456cd796fdbdef0cadb22710b54e0071b6cdf22c07963365baa898267aec517  mmproj-F16.gguf
04f6521d237acdfcc1eec0211b61b22705ed7564e6097b1d664c358aac857eda  Qwen3.8-Flash-Next-MTP-Q8_0.gguf
```

The OrcaRouter IQ4_XS files were also downloaded and verified against their authenticated Hugging Face LFS pointers:

```text
28a99b125cb905fc3bdc06baf6266a56b0cbd1b27e833b9142acc2017b673704  IQ4_XS-00001-of-00003.gguf
2a309e0b112fde96ba3bcba5a6b58cc05e5df7bb7fad5a990eaa51df335b0e43  IQ4_XS-00002-of-00003.gguf
ebc43c58e2eaeba1d5bdf62c8cb1f0eac198c4dc01941f771921edeebf574bc3  IQ4_XS-00003-of-00003.gguf
f0f352a97a62a057f3aecdb597cac664762cea2ca23f7b16ec92eee28c5572d9  mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf
```

## Signal with llama.cpp MTP

Runtime: Unsloth MIX b10715 ROCm gfx1151 (`build 10715`, commit `92cedc867`), `ROCm0`, 64k context, Q8_0 KV, sampling `temperature=0.7`, `top_p=0.95`, `top_k=20`.

The Signal main GGUF loaded without a draft head. Three 256-token runs measured:

```text
21.9 tok/s
21.9 tok/s
22.0 tok/s
```

The downloaded AgentionAI MTP GGUF could not be attached to this llama.cpp build. The server expected `blk.48.nextn.hc_head_norm.weight`; the draft contained the incompatible flat `output_hc_norm.weight` layout. A draft-enabled llama.cpp result is therefore **not claimed**.

## Signal with Halogen MTP

Halogen image: `ghcr.io/peonist-ai/halogen-flash-server:0.11.0`.

The external-GGUF path correctly found the Halogen MTP head `qwen38-flash-next-mtp.hgn`, then rejected the Signal trunk during the lossless GGUF preflight:

```text
gguf: blk.0.ffn_gate_exps.weight: Q4_K is not read by this engine
```

Result: **BLOCKED / incompatible expert quantization**. This is not a 0 tok/s result and no generation benchmark was run. The MTP head itself was found; the trunk was rejected before inference.

## OrcaRouter uncensored with Halogen MTP

Candidate: `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, `IQ4_XS`, three shards, with the same Halogen MTP head and tokenizer.

The Halogen preflight rejected the dense attention trunk:

```text
gguf: blk.0.attn_qkv.weight: Q5_K is not read by this engine
```

Result: **BLOCKED / incompatible dense quantization**. No inference benchmark was run and no tok/s number is reported.

Halogen's external-GGUF loader requires supported expert formats and a supported dense trunk (documented target: dense `Q8_0`; supported expert formats include `IQ4_NL`, `IQ4_XS`, `IQ3_S` and `Q4_0`). The repository's filename `IQ4_XS` does not guarantee that every tensor uses a Halogen-supported type.

## Conclusions

- Signal AP-Q4_K_XL works on the tested ROCm llama.cpp runtime at about **22 tok/s without MTP**.
- Signal's released MTP sidecar is not layout-compatible with this llama.cpp build.
- Signal AP-Q4_K_XL is not accepted by Halogen because its experts include `Q4_K`.
- OrcaRouter IQ4_XS is not accepted by Halogen because its dense `blk.0.attn_qkv.weight` is `Q5_K`.
- Neither Halogen blocker should be reported as a performance result.
- A future Signal or uncensored export with the required Halogen tensor schema is needed for a valid Halogen + MTP speed comparison.

## Reproduction

For the Halogen test, set:

```text
HALOGEN_CHECKPOINT=/models/<first-GGUF-shard>.gguf
HALOGEN_MTP_HEAD=/models/qwen38-flash-next-mtp.hgn
HALOGEN_TOKENIZER=/models/tokenizer
HALOGEN_CTX=65536
HALOGEN_KV_POOL_POSITIONS=65536
HALOGEN_KV_SLOTS=1
```

Then run the `0.11.0` container with the model directory mounted read-only. The preflight error above is emitted before the engine starts listening.

## Heretic2 on Nathanw Vulkan (verified)

The Cygnal `Qwen3.8-Flash-Next-Heretic2-IQ4XS-NGQ4.gguf` loaded successfully in Nathanw `strix-halo-llamacpp-v0.7.6` build 10707 on `gfx1151`.

- Endpoint: `127.0.0.1:18092`
- Main GGUF: 98,403,355,776 bytes (92 GiB on disk)
- Context: 65,536 tokens
- Projector omitted for this text-only test
- MTP: not enabled; this is serial decode
- Raw `/completion` endpoint, `temperature=0`, `n_predict=512`
- 64k runs: 31.61 and 31.61 tok/s predicted
- Earlier 8k runs: 31.52, 31.56, 31.54 tok/s
- The first 65k chat test with the multimodal projector caused Nathanw to exit with `status=11/SEGV`; text-only raw completion then worked at both 8k and 65k. Treat projector/chat-template multimodal serving as a separate unresolved issue.

This confirms Heretic2 is usable on the Nathanw Vulkan route for text inference. It does not yet validate MTP; a llama.cpp-compatible draft GGUF must be tested separately from the Halogen `.hgn` head.

## Decision and current operating configuration (2026-09-20)

The benchmark document and `halogen-assessment.md` were reconciled with the local tests. The important distinction is **official Halogen checkpoint vs. external BYO-GGUF**:

- Official Halogen Qwen includes a quality overlay and is the recommended daily chat + coding-worker route.
- Heretic2 BYO-GGUF can load in Halogen, but the published HumanEval+ result was only `65.2% / 61.0%` versus `84.1% / 79.3%` for the same Heretic2 weights through llama-server. This is an overlay/serving-quality caveat, not evidence that Halogen itself is low quality.
- Heretic2 is therefore kept as an optional uncensored Nathanw profile, not the default shared chat/worker server.
- The failed OrcaRouter external GGUF was removed after the `Q5_K` Halogen preflight blocker; no running service referenced it.

The restored official Halogen service is configured for concurrent use:

```text
HALOGEN_CTX=65536
HALOGEN_KV_POOL_POSITIONS=131072
HALOGEN_KV_SLOTS=2
HALOGEN_MTP_HEAD=loaded by the official checkpoint
```

The health endpoint verified `slots=2`, `kv_pool_positions=131072`, `drafters_available=[serial,mtp]`, with the worker and chat able to occupy separate slots. This is the recommended configuration for a quality programmer plus interactive chat.

## Benchmark-source interpretation

The supplied 12-quantization benchmark reports:

- Heretic2 IQ4_XS NGQ4 via llama-server: `84.1% / 79.3%`, about `4.16 s/problem`.
- Uncensored IQ4_XS NGQ4 via llama-server: `81.7% / 78.7%`.
- Official Halogen with overlay: `82.3% / 78.0%`.
- Heretic2 BYO through Halogen: `65.2% / 61.0%`.
- The article's Halogen quality warning is specific to BYO models without the matching overlay. Its comments also indicate that thinking can be controlled with `enable_thinking=false`; that setting should be included in any future reproduction rather than treating the original thinking-mode result as universal.

The benchmark's reported Halogen speed advantage is real mainly for prefill. It does not by itself justify replacing the official overlay-backed route with an external Heretic2 checkpoint.
