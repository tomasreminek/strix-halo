# Halogen 64k coding worker alongside Ornith 128k

## Measured results

- medium: 31391 input tokens, 65 output tokens, 33.584 s wall time; code tests PASS; cached tokens not reported.
- long: 53391 input tokens, 65 output tokens, 51.869 s wall time; code tests PASS; cached tokens not reported.
- long-repeat: 53391 input tokens, 65 output tokens, 4.142 s wall time; code tests PASS; cached tokens 53384.
- near-64k: 61901 input tokens, 65 output tokens, 241.443 s wall time; code tests PASS; cached tokens not reported.

All four probes retrieved three separated markers and fixed a clamp function that passed five assertions in a read-only, network-disabled container. The synthetic repository is repetitive and the repair is simple. This is not a complex repository or multi-day reliability certificate. The repeat used cache, not an independent cold run. Latency is end-to-end, not decode throughput.

Ornith remained configured at 131072 tokens. Initial concurrent requests exhausted their 256-token budget without final text: these are not functional passes. The final concurrent control returned ORNITH_OK in 0.285 s. Its tiny prompt does not validate two full contexts at once or sustained overlap.

## Configuration

Halogen image ghcr.io/peonist-ai/halogen-flash-server:0.11.0; model halogen-qwen3.8-flash-next; abliterated experts plus overlay; one slot; HALOGEN_CTX=65536; HALOGEN_KV_POOL_POSITIONS=65536; HALOGEN_MAX_TOK=8192; pinned trunk; MTP default. See launcher snapshot alongside raw records. Probes: temperature=0, enable_thinking=false, max_tokens=800.

Server window is distinct from Hermes delegation configuration. The persisted delegation context was previously 32768; publication updates it to 65536. The CLI warns that delegation.context_length is unrecognized, and the installed delegate code does not directly read this key. Therefore this persisted value is NOT proof that Hermes children use 64k; server capacity is verified, agent-side propagation remains unverified. No gateway restart is performed by this publication.

## Mandatory worker policy


When delegating programming to Halogen while Ornith remains resident, copy these rules into the child's task context (do not assume it inherits the parent skill):
- Use one worker at a time, a 65536-token server window, and reserve at least 8192 tokens for output, tools, and handoff; aim to hand off before 50k input tokens. These are conservative operating limits, not a measured stability guarantee.
- Split work into bounded, testable tasks. Read targeted files rather than repeatedly stuffing the whole repository into context.
- After each completed task, run relevant tests and preserve a scoped Git checkpoint on the assigned branch. Never include unrelated user changes or push without task authorization.
- Maintain WORKER_STATE.md in the assigned worktree: goal, branch/commit, changed paths, exact test commands/results, blockers, next step. Update before compression, exit, or retry; resume from disk and verify actual Git state.
- Use a durable supervisor for multi-day work, not one process-local delegate call; bounded rounds must have timeouts, progress logs, stop handling, and limited retries. Do not launch a multi-day job merely by installing these rules.
- Do not resize/restart Ornith or load media/other GPU models. On OOM, repeated timeouts, or lost endpoint, checkpoint and report to the controller; do not restart blindly.
- Report near-limit latency, cache hits, code-test correctness and long-term stability separately. A synthetic retrieval/clamp test is not a multi-day repository-coding certificate.


## Evidence

[Raw JSON, probe script and launcher](../records/benchmarks/worker-context-proof/). The near-64k probe calls probe(1730, "near-64k") from run.py; the suite itself covers the first three probes. No 128k-worker test or multi-day soak was performed.
