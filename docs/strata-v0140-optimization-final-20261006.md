# Strata gfx1151 final configuration screening — local draft

Stock v0.1.40, Orca Uncensored IQ3_XXS, MTP4, official fast environment retained from the prior follow-up. No production routing or persistent launcher changes.

30k input + 420 output:
- Auto+fast: prefill 1288.88 tok/s, decode 41.69 tok/s, request 33.42 s.
- Fast + prefill 16384: prefill 1303.49 tok/s, decode 42.74 tok/s, request 32.91 s.
- Auto+fast + MTP window 8192: prefill 1285.95 tok/s, decode 42.85 tok/s, request 33.20 s.

Selected prefill16384+fast validation:
- 7,600 input: prefill 1170.49 tok/s, decode 43.72 tok/s, request 16.12 s.
- 61,999 input: prefill 1303.96 tok/s, decode 41.00 tok/s, request 57.94 s.
- 126,000 input: prefill 1270.78 tok/s, decode 40.39 tok/s, request 109.83 s; cached decode 41.30 / 41.25 tok/s.

18/18 depth records, 17/17 short checks passed. Controlled cleanup and unchanged routing verified; ports 18081 and 18087 closed. MTP window arm was screened only at 30k; no deep-context conclusion for that arm.

126k request time improves approximately 2.93% against the prior auto+fast observation (113.14 s). This is a small single-sample difference, not a statistically established gain. 64k decode is lower than the prior auto+fast observation despite slightly better prefill; no universal decode winner is claimed. Fast changes numerics; marker/short fixtures do not establish general quality equivalence. Repeated independent new-prefix samples and broader coding/soak checks remain required before promotion.

Raw evidence: `/home/tomasreminek/Projekty/strata-halo-0140/bench/official-halo-20261006/optimization-final-20261006-123824/`. Executable: `optimization_final.py`; configs and logs retained per arm. Systemd outer-supervisor peak is not GPU memory residency evidence. Not published.
