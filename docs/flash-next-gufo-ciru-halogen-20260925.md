# Flash-Next on Hilbert: Gufo, CIRU Orca, Halogen and Ornith (24–25 September 2026)

**Local measurements, not model-card speed claims.** Hardware: Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`), 124 GiB usable UMA, Pop!_OS. `tok/s` below is engine-reported *output decode*, never total prompt+completion divided by request wall time. Synthetic marker retrieval is a narrow correctness gate, not general quality certification. Raw synthetic responses and machine-readable counters are in [`records/benchmarks/flash-next-september-2026/`](../records/benchmarks/flash-next-september-2026/).

## Identity and protocol

- **Gufo / official base**: `unsloth/Qwen3.8-Flash-Next-GGUF` revision `38bb39ee97821de2c9009abb7e93950eec396e66`, UD-Q4_K_XL four shards (111,334,654,784 B total); Gufo container image `ghcr.io/gufo-org/toolboxes/gufo-runtime@sha256:989ab52a190244f08511a3ad0fd46546f2144220c37e6c808ad8008a934ebab5`, source `9cad139`; **serial, MTP off**, one slot. This is the **official base**, not uncensored. All shards were size/SHA256 verified. Runtime `--context 131584 --think off`.
- **Halogen / existing uncensored worker**: native Qwen3.8 Flash-Next HGN with abliterated expert patch and overlay, Halogen 0.11.0, production MTP on, one 131,072-token slot (`HALOGEN_CTX` and KV pool), `:18081`. This is a different checkpoint, quant and decoder; comparison describes *available configurations*, not isolated engine speed.
- **CIRU / Orca derivative**: `jcbtc/Qwen3.8-Flash-CIRU-STRIX-Orca` revision `8a40c7e9d72f73eb20b802ed26a7ce92c1f351a5`; custom mixed-precision main GGUF 79,397,818,912 B, external PLE 52,429,053,952 B, matching Q8 MTP head 4,135,893,440 B; all final SHA256 verified. CIRU v4.4.1 Nix binary invoked via host ELF loader; packaged Nix HIP/ROCr did not detect the GPU on Pop!_OS, so the existing ROCm 7.2.4 libraries were selected first. One slot, F16 KV, PLE cache 4096 MiB, `on-direct`, QSA, MTP depth 4 for speculative arms. Short 8k-configured arms used a **47-token prompt** (not a filled 8k prompt). Long arm: 65,536 context, `-b 8192 -ub 8192`; no vision projector/hotfix tested.
- **Ornith / chat counterpart**: abliterated 9B ROCmFP4 STRIX_LEAN, `:18083`; short simultaneous request used to establish both services could respond. Not every coexistence arm is a long-duration soak.
- The matched marker fixture asks for the three values near beginning, middle and end of a deterministic synthetic corpus plus prose. Requests use temperature 0, output cap 420; actual prompt length is ~9.5k / ~62.4k / ~127.5k depending on template. Some CIRU replies stop naturally at 399 tokens. The original Gufo script falsely required label prefixes (`START=` etc.); checking the *values* in raw visible output confirms all measured Gufo/Halogen/CIRU marker retrievals passed.

## Matched Gufo vs Halogen (without Ornith)

| Input tokens (Gufo / Halogen) | Gufo cold decode | Gufo warm decode | Gufo cold wall / prefill | Halogen cold decode | Halogen warm decode | Halogen cold wall / prefill |
|---|---:|---:|---:|---:|---:|---:|
| 9,551 / 9,591 | 25.74 | not run | 22.9 s / 6.51 s | 32.91 | 36.96, 36.96 | 21.41 s / 8.64 s |
| 62,397 / 62,437 | 22.94 | 22.88, 22.89 | 63.8 s / 45.32 s | 31.41 | 34.64, 34.64 | 66.48 s / 53.05 s |
| 127,525 / 127,565 | 21.05 | 20.99, 20.98 | 113.47 s / 93.24 s | 30.54 | 33.25, 33.26 | 125.47 s / 111.56 s |

Each completed 420 output tokens and contained all three requested marker values. **Halogen wins decode and cached requests; Gufo wins cold, uncached long-prompt wall time in this fixture.** Neither model is an unconditional speed winner. Gufo weights were therefore not deleted. Gufo's earlier direct tool call and isolated Hermes tool turn passed, but no Gufo+Ornith simultaneous arm was run; that gap remains **untested**.

## CIRU Orca locally measured

| CIRU arm | Prompt / output tokens | Prefill | Decode | Wall / result |
|---|---:|---:|---:|---|
| 8k configured, **no MTP**, isolated, cold | 47 / 420 | 0.564 s | **23.67 tok/s** | 18.27 s; output valid |
| same, cached warm | 47 / 420 | 0.086 s (4 new) | **27.37 tok/s** | 15.44 s |
| 8k configured, **Q8 MTP4**, isolated, cold | 47 / 420 | 0.540 s | **30.94 tok/s** | 14.09 s; 272 / 582 drafted tokens accepted |
| same, cached warm | 47 / 420 | 0.089 s (4 new) | **36.31 tok/s** | 11.68 s; same 272 / 582 drafted |
| same cached prompt, concurrent Ornith generation | 47 / 420 | 0.110 s (4 new) | **18.94 tok/s** | 22.24 s; Ornith replied in 1.76 s |
| 65,536 slot, MTP4, isolated, cold marker corpus | 62,397 / 399 | **207.87 s (300.18 tok/s)** | **17.24 tok/s** | 230.99 s; three markers pass; 249 / 608 drafted accepted |
| same cached warm | 62,397 / 399 | 0.176 s (4 new) | **19.12 tok/s** | 21.48 s; markers pass |
| same cached corpus, concurrent Ornith generation | 62,397 / 399 | 0.587 s (4 new) | **13.75 tok/s** | 29.69 s; Ornith replied in 1.45 s; markers pass |

The first 64k attempt at `-b/-ub 2048` timed out after 125 s with only ~38.9k input tokens processed; its partial prefill logs are diagnostic, **not** `0 tok/s`. The retry at 8192 completed, but was still much slower at 64k than Gufo or Halogen. **No 128k CIRU inference result**: the 64k concurrent arm already drove available host RAM to ~5.7 GiB and swap use to ~3.9 GiB (GTT ~104 GB), so 128k with Ornith was not a safe production gate. At 8k-configured short use both fitted (GTT ~92.5 GB); this does not certify deep-context coexistence.

## Real Ornith + Halogen control and decision

A concurrent, **cold ~62k Halogen prompt** and a short Ornith reply passed: Halogen 62,437 input / 420 output, prefill **1,147.64 tok/s** (~54.40 s), decode **30.95 tok/s**, wall **68.08 s**; Ornith answered `ORNITH_CHAT_OK` in **1.81 s**. Both services remained active; after CIRU teardown available host RAM was ~88 GiB and GTT ~26.25 GB, swap ~1.0 GiB. These memory figures are observed snapshots, not per-model VRAM footprints. Units `ornith.service` and `qwen38-flashnext.service` are enabled and were healthy on `:18083` and `:18081`; no actual machine reboot or multi-day soak was performed. The global Telegram route was not changed. Paused C&C automation was not reactivated.

**Operational choice for this tested workload: Ornith for chat/task assignment + uncensored Halogen for worker.** CIRU is a real, locally runnable research option but loses long-context prefill/decode here and pressures UMA when paired with Ornith. Gufo base is separately valuable for cold prefill; it is not an uncensored replacement. Do not merge the older CIRU v3 3.3 tok/s historical result with this v4.4.1 MTP4 measurement or promote CIRU based on a publisher graph. Full Hermes quality/coding gate for CIRU and 128k CIRU remain unverified.

## Reproduction boundaries

Synthetic request generator: [`fixture-probe.py`](../records/benchmarks/flash-next-september-2026/fixture-probe.py); request corpus SHA256 `a217be934d60d5bf917ef60f65e0fd69dc92d2bdef36ed21d6fc2196204bcd0b`. Raw API responses and summary JSON are linked from the [record directory](../records/benchmarks/flash-next-september-2026/README.md). Original local server journals and full Hermes session export are **not published** (operational/private data); only synthetic prompt/output and timing counters are included. Local complete evidence remains under `/mnt/data/Projekty/gufo-eval/results/unsloth-gufo/`.
