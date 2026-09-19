# Splitting one Qwen3.8-Flash-Next into a chat model and a working worker

**Measured and running 2026-09-19 on AMD Ryzen AI MAX+ 395 (gfx1151), 128 GiB unified memory.**

The question this answers: can the *same* local Flash-Next model be the model you chat with **and** a background worker that grinds on long coding jobs, without one starving the other? Yes — with one server instance, two KV slots, and routing discipline in the agent layer. This is exactly how this box is configured right now.

## The mental model

One GPU box, one heavy model, two very different jobs:

| Role | Job shape | What matters |
|---|---|---|
| **Chat** | Short turns, interactive, Telegram/CLI | Latency per turn, conversation continuity |
| **Worker** | Long output-heavy coding runs: generate files, run gates, iterate | Sustained decode throughput, big context, checkpointing |

You do **not** need two servers or two models. The Halogen server supports multiple KV slots, so one loaded model can hold the chat conversation in one slot and a worker session in another simultaneously. The split happens in three layers:

1. **Server layer** — one `halogen-flash-server` container with `HALOGEN_KV_SLOTS=2`.
2. **Routing layer** — the agent framework keeps chat and delegation as separate config routes that both point at the same endpoint.
3. **Discipline layer** — the chat side never runs long jobs inline; long jobs are dispatched as delegated/headless sessions and supervised.

## Layer 1: the server

One container, one model, two slots (this is the live configuration):

```bash
docker run -d --name halogen-qwen38 \
  -p 127.0.0.1:18081:8731 \
  --device /dev/kfd --device /dev/dri \
  --group-add "$(getent group video | cut -d: -f3)" \
  --group-add "$(getent group render | cut -d: -f3)" \
  --ipc=host --ulimit memlock=-1:-1 \
  -e HALOGEN_CTX=65536 \
  -e HALOGEN_KV_POOL_POSITIONS=131072 \
  -e HALOGEN_KV_SLOTS=2 \
  -e HALOGEN_MAX_TOK=32768 \
  -e HALOGEN_PROMPT_CACHE=2 \
  -e HALOGEN_VISION_TOWER=1 \
  -v "$MODEL_DIR:/models:ro" \
  ghcr.io/peonist-ai/halogen-flash-server:0.11.0 all
```

Key knobs for the split:

- **`HALOGEN_KV_SLOTS=2`** — the load-bearing setting. Slot A carries the chat conversation, slot B carries the worker session. Without a second slot, the worker evicts the chat KV (or queues behind it) and the interactive feel dies.
- **`HALOGEN_KV_POOL_POSITIONS=131072`** with `HALOGEN_CTX=65536` — the pool is sized so two concurrent sessions of real depth fit; a per-session 64k context alone would not be enough for two.
- **`HALOGEN_MAX_TOK=32768`** — per-response cap. Keep this in mind on the worker side (see the pitfall below).

Verify: `curl -s http://127.0.0.1:18081/v1/models` → `halogen-qwen3.8-flash-next`.

## Layer 2: routing chat vs worker

In Hermes (the agent framework on this box) the split is literally two config blocks pointing at the same endpoint. Chat route:

```yaml
model:
  default: qwen-flash-next
  provider: custom
  base_url: http://127.0.0.1:18081/v1
  api_key: local
  context_length: 65536
```

Worker route:

```yaml
delegation:
  model: qwen-flash-next
  provider: custom
  base_url: http://127.0.0.1:18081/v1
  api_key: local
  reasoning_effort: low
  max_concurrent_children: 1
  context_length: 65536
```

Same model, same server — different *policies*. The chat route optimizes interactivity; the delegation route is what `delegate_task` children and dispatched worker sessions use, with its own iteration budget, reasoning effort and concurrency cap. `max_concurrent_children: 1` matters: two slots means one chat + one worker, not two workers plus chat.

The same shape works with any OpenAI-compatible framework that separates "interactive model" from "subagent model": point both at the one endpoint, cap worker concurrency to `KV_SLOTS - 1`.

## Layer 3: operational discipline

The routing only pays off if the chat side actually delegates:

- **Chat never grinds.** Long code generation, refactors, gate-running loops go to the worker route — never inline in the chat turn.
- **Worker = headless session with a contract.** Dispatch the worker as a headless CLI session (`hermes -c "<task file>"` style) against the same endpoint, with the task written as a file: goal, ownership rules, verification gates, commit message. The worker commits checkpoints; the chat side reviews.
- **A supervisor watches.** The chat/agent side periodically checks: is the worker process alive, are gates green, has it stalled or looped. If the worker dies mid-task, its WIP is already committed and a fresh worker resumes from the checkpoint — the split survives crashes because state lives in git, not in the KV cache.
- **Context budget is per-slot.** The chat conversation and the worker each get their own context window; they do not share tokens. But each must fit its own slot — see pitfalls.

## Free bonus: a cloud helper that costs zero GPU

Because the worker is local and the helper is cloud, you can add a third agent that never touches the unified memory: Antigravity CLI (`agy`) runs Gemini-family models remotely.

```bash
agy -p --dangerously-skip-permissions --print-timeout 45m \
  "Read TASK.md, implement, run the gates until green, commit."
```

This runs *concurrently* with the local Flash-Next worker with zero contention — the local GPU never sees it. Use it as a second pair of hands on the same repo (different worktree or disjoint files) or as a cross-check reviewer of the local worker's diff.

## Pitfalls measured the hard way (2026-09-19)

1. **`max_tokens` vs slot room.** A worker sent `max_tokens=8192` with a 29,062-token prompt against a 32,768-token room and got HTTP 400: `prompt is 29062 tokens and the context is 32768, leaving room for 3706`. The framework's own context accounting (131k) disagreed with the server's slot geometry. Rule: on the worker side, cap requested completion below `min(HALOGEN_MAX_TOK, slot_room − prompt_tokens)`, or keep worker prompts under ~24k when asking for 8k completions.
2. **Headless `agy` auto-denies file reads.** Without `--dangerously-skip-permissions` (or explicit `permissions.allow` rules in `settings.json`), a headless print run dies with *"a tool required the read_file permission that headless mode cannot prompt for"*. Always pass the skip flag or pre-allow the target paths.
3. **Do not run two heavy local models "just in case."** The split is one model, two slots — not two servers. Extra llama.cpp instances compete for the same unified memory and both degrade.
4. **Worker WIP must be committed before supervision continues.** Uncommitted worker state is lost state. The checkpoint-then-review loop is what makes the chat side able to fire, restart or replace the worker at any time.

## What this buys you

- One 124 GiB model loaded once serves both roles — no second cold load (~2 min each), no double memory.
- Chat stays interactive while the worker burns a full slot on a 45-minute coding run.
- The worker's failure domain is isolated: it can crash, overflow its context, or loop, and the chat conversation is untouched.
- A cloud helper adds parallel hands without touching the GPU budget at all.

Related: [qwen38-halogen.md](qwen38-halogen.md) (engine provenance, benchmark matrix), [model-comparison.md](model-comparison.md).
