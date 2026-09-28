# Gufo PR #91 versus Halogen: complete HTTP requests (28 September 2026)

**Local measurement, not the PR author's claim.** On this particular three-marker corpus, **the existing uncensored Halogen worker won cold request wall time, cached request wall time and output decode at all three tested depths**. PR #91 improved the *strix-llama.cpp* Gufo fork against its own unpatched master; it did not make that fork faster than Halogen. The older, faster **native Gufo container** measurement is a third runtime and must not be attributed to this PR.

## Identity and method

Hardware: Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124 GiB usable UMA, Pop!_OS. Gufo: official *base* `unsloth/Qwen3.8-Flash-Next-GGUF` UD-Q4_K_XL four-shard model (not uncensored), identical local weights in both fork builds. Fork master `ec01a7d`; PR #91 branch `e652a3c`; both HIP builds target `gfx1151` with isolated ROCm 7.2.4. `llama-server -c 131584 -np 1 -b 4096 -ub 4096 -ngl 99 -fa on -ctk f16 -ctv f16 -lm dio -lzm on`, one local test port; no MTP. Gufo API request explicitly used `chat_template_kwargs.enable_thinking=false`. Halogen: native HGN 0.11.0 with abliterated expert patch/overlay, MTP on, one 131,072-token slot; existing `:18081` service. No production routing changes.

Identical synthetic [fixture](../records/benchmarks/flash-next-september-2026/fixture-probe.py) generated 5k, 33k, 67.5k characters of source text; the servers reported approximately 9.5k, 62.4k, 127.5k prompt tokens after their respective chat templates. The instructions requested three exact marker values then at least 300 visible tokens of prose. `temperature=0`, `max_tokens=420`, nonstreaming chat completion. One cold/new-prefix request and its immediate identical cached repeat **per engine and depth**; no independent replicate series. Each row below passed the three-value visible-output gate in both requests. Output decode is engine-reported `predicted_per_second`, **not** completion count divided by request wall time. Cache hits are engine-reported; the slightly different token counts reflect template differences. Raw responses, timings, request flags and prompt hashes are in [records/benchmarks/gufo-pr91-halogen-20260928/](../records/benchmarks/gufo-pr91-halogen-20260928/).

| Engine / corpus | Prompt tokens | Cold wall / prefill | Cold decode | Cached wall / reused tokens | Cached decode |
|---|---:|---:|---:|---:|---:|
| Gufo stock llama.cpp · 5k chars | 9,551 | 33.04 / 14.41 s | 22.51 tok/s | 18.63 s / 9,547 | 22.65 tok/s |
| Gufo **PR #91** llama.cpp · 5k chars | 9,551 | 31.02 / 11.92 s | 22.01 tok/s | 19.07 s / 9,547 | 22.12 tok/s |
| **Halogen** · 5k chars | 9,591 | **21.71 / 8.81 s** | **32.64 tok/s** | **11.45 s / 9,586** | **36.91 tok/s** |
| Gufo stock llama.cpp · 33k chars | 62,397 | 113.65 / 94.46 s | 22.05 tok/s | 19.01 s / 62,393 | 22.24 tok/s |
| Gufo **PR #91** llama.cpp · 33k chars | 62,397 | 96.38 / 76.82 s | 21.60 tok/s | 19.46 s / 62,393 | 21.71 tok/s |
| **Halogen** · 33k chars | 62,437 | **66.85 / 53.38 s** | **31.36 tok/s** | **12.27 s / 62,432** | **34.56 tok/s** |
| Gufo stock llama.cpp · 67.5k chars | 127,525 | 221.88 / 202.10 s | 21.67 tok/s | 19.45 s / 127,521 | 21.79 tok/s |
| Gufo **PR #91** llama.cpp · 67.5k chars | 127,525 | 181.53 / 161.18 s | 21.15 tok/s | 19.90 s / 127,521 | 21.29 tok/s |
| **Halogen** · 67.5k chars | 127,565 | **126.11 / 112.15 s** | **30.45 tok/s** | **12.83 s / 127,560** | **33.20 tok/s** |

PR versus fork stock reduced measured cold prefill duration at ~127.5k from 202.10 to 161.18 s (~20%). The separate `llama-bench` experiment measured +27–31% *synthetic prompt token/s* with 2k new tokens at depths 0/32k/64k; that is **not** a full request speedup. At ~127.5k, Gufo PR's 181.53 s full cold request was much slower than Halogen's 126.11 s in the matched API probe.

### Runtime distinction and correctness boundary

An [earlier Gufo **native container** comparison](flash-next-gufo-ciru-halogen-20260925.md) measured 113.47 s cold ~127.5k request versus historical Halogen 125.47 s. That result remains valid **for its own runtime and configuration**. It is not the PR #91 llama.cpp result and is not a reason to replace the existing uncensored Halogen worker with this fork.

The first Gufo PR API probe omitted the thinking-disable flag: all 420 tokens went to reasoning, with **no visible output and no marker values**. These failed diagnostic outputs are retained locally but excluded from the valid comparison; the corrected six PR requests all emitted visible prose and all three values. This marker task is a narrow retrieval check, not an uncensored-behavior, coding, tool-use, general quality, long-running stability, concurrent Ornith or boot test. Halogen and Ornith were stopped only for the exclusive Gufo tests and both were restored with `/health` HTTP 200 afterward.

**Raw artifact format:** each `*-1.json`/`*-2.json` contains the visible answer, complete timing and usage data, wall seconds, and marker flags; `*-request-metadata.json` contains fixture hashes and nonprompt request settings. The raw files are synthetic, not private user prompts. `fixture-probe.py` in the September record regenerates the prompt body.
