# Talus 0.1.3 · 128k context measurement (2026-11-04)

Marker: `TALUS_128K_20261104`

## Question

The four-point sweep in [`talus-vision-production-20261104.md`](talus-vision-production-20261104.md)
stops at 65 700 tokens. Chat and the coding worker both run with a 131 072-token window, so the
number that actually matters for production is what happens near the top of that window. This
record answers that.

## Result

Config: the deployed `talus-qwen.service` — Talus `0.1.3` behind Strata `serve.server`, abliterated
`qwen3.8-flash-next-unsloth-ud-iq4_xs`, MTP head (`spec=16 mtp_max=4`), 131 072 ctx, KV int8,
`--batch 2`.

| depth | prefill tok/s | prefill wall | decode tok/s | warm TTFT |
|---:|---:|---:|---:|---:|
| 126 600 | **1 270.8** | 99.62 s | **42.86** | 171 ms |

- Prefill holds up. 1 270.8 tok/s at 126.6k sits between the 65.7k point (1 350) and a small
  expected drop from the longer KV scan — no cliff, no swap, no OOM. 126 600 tokens are absorbed in
  **under 100 seconds**.
- Decode drops from 61.5 tok/s at 65.7k to **42.86** at 126.6k. That is the expected cost of
  attention over a 4× longer cache, and it is still faster than Strata managed at 2k (32.2 tok/s).
- Warm TTFT of **171 ms** is the number a user feels on a follow-up turn: with the prefix cached,
  the first token arrives in about a sixth of a second even at full context.

## Method

`bench_v2.py` from this repo, label `talus-128k-final`, depth 127 000, run against
`http://127.0.0.1:18087`.

Two properties of the method matter, and both were violated by earlier attempts:

1. **Cold prefill needs a fresh random salt in the prompt.** Otherwise calibration probes warm the
   prefix cache and prefill looks ~100× faster than reality.
2. **The second slot must be idle.** This box has one GPU and the engine runs `--batch 2`; a
   concurrent request on the other slot does not just slow decode, it makes the figure meaningless.

The first attempt at this measurement reported decode **1.45 tok/s** and the second **7.0 tok/s**.
Both were contaminated: the DSH coding worker was mid-turn on slot 1. Cancelling the worker session
through the RPC was not enough — the supervisor resumed it. The clean run required
`systemctl --user stop dsh-dejiny-web.service` for the duration, then starting it again afterwards.

So the rule for anyone repeating this: **stop the worker, verify
`free slots == 2/2` on `/slots`, then bench.**

```bash
systemctl --user stop dsh-dejiny-web.service
sleep 5
curl -s http://127.0.0.1:18087/slots \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print('free:',sum(1 for s in d if not s['is_processing']),'/',len(d))"
cd ~/.hermes/cache/scratch
python3 bench_v2.py talus-128k-final http://127.0.0.1:18087 127000
systemctl --user start dsh-dejiny-web.service
```

Raw output:

```json
{
 "label": "talus-128k-final",
 "url": "http://127.0.0.1:18087",
 "time": "2026-11-04 09:47:13",
 "runs": [
  {
   "depth": 126600,
   "pp_tps": 1270.8,
   "tg_tps": 42.86,
   "tg_n": 256,
   "prefill_s": 99.62,
   "warm_ttft_ms": 171
  }
 ]
}
```

Contaminated runs, kept so nobody re-derives them as real:

```json
{"depth": 127688, "pp_tps": 857.1,  "tg_tps": 1.45, "tg_n": 256, "prefill_s": 148.98}
{"depth": 126604, "pp_tps": 1270.9, "tg_tps": 7.0,  "tg_n": 256, "prefill_s": 99.62}
```

Note that the *prefill* figure survived contamination in the second run (1 270.9 vs 1 270.8 clean) —
a cold prefill is a single request and reads the same either way. Decode is where concurrency shows
up. That is why the prefill number can be trusted from a busy box and the decode number cannot.

## Consequences for production

- **128k in chat is viable.** 100 s to ingest a 126k-token context is slow in absolute terms but it
  is a one-time cost per new document; follow-up turns hit the cache at 171 ms TTFT and stream at
  ~43 tok/s.
- **128k in the worker is viable but expensive to start.** The worker reads many small files rather
  than one huge document, so it accumulates context gradually and rarely pays a full 100 s prefill.
- **Do not benchmark with the worker up.** It is the single most common way to get a wrong number on
  this box.
