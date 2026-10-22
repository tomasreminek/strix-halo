#!/usr/bin/env python3
"""
bench_maya.py -- measure a Project Maya server (DeepSeek-V4.1-Flash-1017, "Maya-S"
GGUF, served by maya.py on the AMD box) with the same harness as bench.py, so a row
here lines up with a row from the strix-halo recipe.

The measuring rules are inherited unchanged from bench.py, because the point of the
port is comparability:

  * token counts come from usage.completion_tokens, never from chunk counts;
  * every non-one-shot run gets a fresh, unique prompt whose length is verified with
    the SERVER's own tokenizer, so two configs are compared on the same prompt;
  * the seeds include the label, so two rows taken back to back on one server do not
    share prompts (a repeat is served warm -- from any prefix cache and from an expert
    arena the first run already filled);
  * TTFT / TPOT / decode tok/s are the same formulas as in bench.py.

What changed is the API surface. Project Maya is a different server, so:

  * prompt length: bench.py asks POST /v1/debug/prompt for prompt_tokens; Maya has
    POST /api/tokens, which renders the same chat template and tokenizer and runs
    nothing. It answers with {"tokens": N}.
  * engine stats: bench.py reads the server's x_engine_stats out of the SSE stream
    (acceptance length, expert hit rate, NVMe GB, engram rows). Maya has no such
    field. The equivalent facts come from GET /metrics, which reports the engine's
    own counters: the expert tiers, the VRAM/RAM split of the routed experts, the
    Engram lookups, the totals and the hardware. The mapping is imperfect -- Maya
    does not publish an acceptance length at all -- so the fields Maya cannot supply
    are left null and the whole raw /metrics snapshot is kept next to them.
  * ignore_eos: Maya's server does not know the field. A run that asks for a fixed
    output length therefore gets max_tokens, and the run's finish_reason says whether
    the model stopped on its own ("stop") or was cut at the cap ("length"). The
    --fixed-len flag makes that explicit: if the model stopped by itself the length
    is NOT pinned, and the JSON summary says so in a warning, because two configs are
    then compared on two different amounts of work.
  * thinking: Maya's primary switch is the top-level enable_thinking (bool); it also
    accepts chat_template_kwargs.thinking. reasoning_effort is Maya's own enum
    (none|low|high|max), not the 1-100 number the strix-halo server takes, so --effort
    accepts both and maps a number onto the enum.

Usage:
    python3 bench/bench_maya.py --base http://127.0.0.1:18091 --workload prose --out results/maya-prose.json
    python3 bench/bench_maya.py --base http://127.0.0.1:18091 --workload random --isl 1024 --osl 128
    python3 bench/bench_maya.py --base http://127.0.0.1:18091 --workload angry-birds --label maya
"""
import argparse, hashlib, json, os, random, re, statistics, string, sys, time
from urllib import request as urlrequest

HERE = os.path.dirname(os.path.abspath(__file__))
# The repo root is two levels above bench/ (deepseek-v41-flash/bench -> repo), so the
# one-shot artefacts land in the repo's results/oneshots/ next to the other recipes'.
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
ONESHOT_DIR = os.path.join(REPO_ROOT, "results", "oneshots")


def post(base, path, payload, api_key=None, timeout=3600):
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urlrequest.Request(base.rstrip("/") + path, data=data, headers=headers)
    return urlrequest.urlopen(req, timeout=timeout)


def get_json(base, path, api_key=None, timeout=60):
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    req = urlrequest.Request(base.rstrip("/") + path, headers=headers)
    with urlrequest.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def token_len(base, prompt, model, api_key, thinking):
    """Exact rendered-prompt length from Maya's own tokenizer.

    /api/tokens runs the chat template and the tokenizer and returns the count --
    but never touches the engine, so it is free where a prefill would be minutes of
    expert streaming. The answer's key is "tokens" (bench.py's /v1/debug/prompt used
    "prompt_tokens"); both are accepted so a future rename does not silently return
    None.
    """
    try:
        out = post(base, "/api/tokens",
                   {"model": model, "messages": [{"role": "user", "content": prompt}],
                    "enable_thinking": bool(thinking),
                    "chat_template_kwargs": {"enable_thinking": bool(thinking)}}, api_key, timeout=120)
        obj = json.loads(out.read())
        n = obj.get("prompt_tokens")
        if n is None:
            n = obj.get("tokens")
        return n
    except Exception:
        return None


def make_prompt(target_tokens, seed):
    """Unique, non-repetitive text so nothing is prefix-cached or run-merged."""
    rnd = random.Random(seed)
    words = []
    for i in range(target_tokens * 3 + 64):
        w = "".join(rnd.choice(string.ascii_lowercase) for _ in range(rnd.randint(3, 9)))
        words.append(f"{i}:{w}")
    return " ".join(words)


def fit_prompt(base, model, isl, seed, api_key, thinking):
    """Scale a unique word list until Maya's own tokenizer reports ~isl.

    Ratio iteration, not a bounded bisect: each filler item is several tokens, so a
    word-count bisect with naive bounds saturates at its ceiling and silently hands
    back a prompt twice the intended length.
    """
    pool = make_prompt(isl, seed).split()
    words = min(len(pool), max(16, isl // 2))
    best_txt, best_n = None, None
    for _ in range(8):
        txt = " ".join(pool[:words])
        n = token_len(base, txt, model, api_key, thinking)
        if n is None:
            return txt, None
        if best_n is None or abs(n - isl) < abs(best_n - isl):
            best_txt, best_n = txt, n
        if abs(n - isl) <= max(8, isl // 200):      # within 0.5%
            return txt, n
        scaled = int(words * (isl / max(n, 1)))
        words = max(16, min(len(pool), scaled))
    return best_txt, best_n


# The one-shot prompts are copied verbatim from tools/make_corpus.py::ONE_SHOTS
# (and from bench.py). Do not reword them: the routing trace in results/ was taken on
# these exact strings, so changing them makes the hit rates incomparable.
ONE_SHOTS = {
    "angry-birds": "Write a complete Angry Birds style game as a single self-contained HTML file: canvas rendering, "
                   "a slingshot with drag-to-aim, projectile physics with gravity, destructible block structures, "
                   "pigs as targets, a score counter, and a restart button. No external libraries or assets.",
    "mario": "Write a complete side-scrolling Mario style platformer as a single HTML file with inline JavaScript: "
             "keyboard controls, jumping with gravity, moving enemies you can stomp, coins, a scrolling level, "
             "and a win condition. No external libraries.",
}

WORKLOADS = {
    # Short prompt, long natural generation -- the number that matches how the
    # box is actually used day to day, and what a speculative drafter is good at.
    "prose": "Write a detailed, flowing essay of about 900 words on how tidal "
             "forces shaped the evolution of coastal ecosystems. Use full "
             "paragraphs and continuous prose, no bullet points or headings.",
    "code":  "Write a complete, production-quality Python module implementing an "
             "LRU cache with a TTL per entry, thread safety, and an eviction "
             "callback. Include full docstrings, type hints, and a pytest suite "
             "covering expiry, eviction order, and concurrent access.",
}
WORKLOADS.update(ONE_SHOTS)
ALL_WORKLOADS = ["random"] + sorted(WORKLOADS)

# The stats bench.py keeps per run. Maya does not publish an acceptance length, so
# that one stays null; the rest is mapped from /metrics (see metrics_snapshot).
HEADLINE_STATS = ["accept_len_mean", "expert_hit_rate", "nvme_gb", "engram_rows"]

# Maya's reasoning_effort enum. A number (bench.py's 1-100) is mapped onto it.
EFFORT_LEVELS = ("none", "low", "high", "max")


def map_effort(effort):
    """--effort as bench.py takes it (1-100) or as Maya takes it (none|low|high|max)."""
    if effort is None:
        return None
    if isinstance(effort, str):
        s = effort.strip().lower()
        if s in EFFORT_LEVELS:
            return s
        if s.isdigit():
            effort = int(s)
        else:
            raise ValueError(f"effort must be none|low|high|max or 1-100, got {effort!r}")
    if effort <= 33:
        return "low"
    if effort <= 66:
        return "high"
    return "max"


def metrics_snapshot(base, endpoint, api_key):
    """GET /metrics: Maya's facts about the engine, the tiers, the totals, the hardware.

    Everything the summary needs that Maya can supply is read here, plus the whole
    snapshot, so a number that was not mapped can still be read out of the JSON later.
    """
    try:
        m = get_json(base, endpoint, api_key)
    except Exception as e:
        return None, {"error": f"{type(e).__name__}: {e}"}
    tiers_now = ((m.get("tiers") or {}).get("now") or {})
    engine = m.get("engine") or {}
    live = m.get("live") or {}
    totals = m.get("totals") or {}
    hardware = m.get("hardware") or {}
    stats = {
        # Maya publishes no acceptance length (no speculative-decoding counter here).
        "accept_len_mean": None,
        # Share of the routed experts found in VRAM: the closest thing to bench.py's
        # expert hit rate, and the number that decides how much comes off the disk.
        "expert_hit_rate": tiers_now.get("vram_hit"),
        # MB the storage read for a token -> GB, as bench.py's nvme_gb.
        "nvme_gb": (tiers_now["disk_mb"] / 1024.0) if isinstance(tiers_now.get("disk_mb"), (int, float)) else None,
        # The n-gram memory's lookups: the closest thing to bench.py's engram rows.
        "engram_rows": engine.get("engram_lookups"),
    }
    extra = {
        "engine_expert_slots": engine.get("expert_slots"),
        "engine_cpu_experts": engine.get("cpu_experts"),
        "engine_ram_experts": engine.get("ram_experts"),
        "engine_engram_layers": engine.get("engram_layers"),
        "live_prefill_tok_s_mean": live.get("prefill_tok_s_mean"),
        "live_tok_s": live.get("tok_s"),
        "totals_decode_ms": totals.get("decode_ms"),
        "totals_prompt_ms": totals.get("prompt_ms"),
        "totals_output_tokens": totals.get("output_tokens"),
        "totals_prompt_tokens": totals.get("prompt_tokens"),
        "totals_requests": totals.get("requests"),
        "hardware_disk_read_mb": hardware.get("disk_read_mb"),
        "hardware_ram_used": hardware.get("ram_used"),
    }
    return {**stats, **extra}, m


def run_once(base, model, prompt, osl, api_key, thinking, effort, temperature, seed=None,
             ignore_eos=False):
    """One streamed chat completion. Returns timings + what the server reported.

    Maya does not know ignore_eos, so it is never sent: the fixed length comes from
    max_tokens, and the run's finish_reason tells us whether the model stopped on
    its own. The caller turns that into a warning.
    """
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": osl,
        "temperature": temperature,
        "top_p": 0.95,
        "stream": True,
        "stream_options": {"include_usage": True},
        # Maya's thinking switch: the OpenAI adapter reads it from
        # chat_template_kwargs.enable_thinking (the top-level "enable_thinking" is
        # ignored on the DeepSeek path), and the chat_template_kwargs.thinking
        # spelling is accepted as well. Both are sent so the request is unambiguous.
        "enable_thinking": bool(thinking),
        "chat_template_kwargs": {"enable_thinking": bool(thinking), "thinking": bool(thinking)},
    }
    if effort is not None:
        # reasoning_effort sets the budget without flipping thinking back on.
        body["reasoning_effort"] = effort
    if seed is not None:
        body["seed"] = seed
    if ignore_eos:
        # Maya's server has no ignore_eos field, so it is not sent -- max_tokens
        # caps the run and the finish_reason below says whether the cap was hit.
        pass
    t0 = time.perf_counter()
    ttft = None
    completion_tokens = None
    reasoning_tokens = None
    finish_reason = None
    timings = {}
    content, reasoning = [], []
    resp = post(base, "/v1/chat/completions", body, api_key)
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if chunk == "[DONE]":
            break
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if obj.get("error"):
            raise RuntimeError(f"server error mid-stream: {obj['error']}")
        # Maya's own timings ride the last chunk: the prompt read and the decode,
        # with the rates the engine measured (the wall-clock numbers below are ours).
        if obj.get("timings"):
            timings = obj["timings"]
        if obj.get("usage"):
            completion_tokens = obj["usage"].get("completion_tokens")
            details = obj["usage"].get("completion_tokens_details") or {}
            reasoning_tokens = details.get("reasoning_tokens")
        ch = obj.get("choices") or []
        if ch:
            if ch[0].get("finish_reason"):
                finish_reason = ch[0]["finish_reason"]
            d = ch[0].get("delta") or {}
            if d.get("content"):
                content.append(d["content"])
            if d.get("reasoning_content"):
                reasoning.append(d["reasoning_content"])
            if ttft is None and (d.get("content") or d.get("reasoning_content")):
                ttft = time.perf_counter() - t0
    total = time.perf_counter() - t0
    if not completion_tokens:
        raise RuntimeError("server returned no usage.completion_tokens -- cannot measure honestly")
    if ttft is None:
        ttft = total
    decode_s = max(total - ttft, 1e-9)
    tpot_ms = (decode_s / max(completion_tokens - 1, 1)) * 1000.0
    return {
        "ttft_ms": ttft * 1000.0,
        "tpot_ms": tpot_ms,
        "decode_tok_s": (completion_tokens - 1) / decode_s,
        "completion_tokens": completion_tokens,
        "reasoning_tokens": reasoning_tokens,
        "finish_reason": finish_reason,
        "total_s": total,
        "x_engine_stats": {},          # Maya has no x_engine_stats: see metrics_raw
        "server_timings": timings,
        "_content": "".join(content),
        "_reasoning": "".join(reasoning),
    }


# ---------------------------------------------------------------------------
# One-shot artefacts
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"```(?:html|HTML)?\s*\n(.*?)```", re.S)


def extract_artifact(text):
    """Return (body, extension) -- a playable HTML file when one is in there."""
    for block in _FENCE.findall(text):
        if re.search(r"<!doctype html|<html|<canvas", block, re.I):
            return block.strip() + "\n", "html"
    m = re.search(r"(<!doctype html.*|<html.*)", text, re.I | re.S)
    if m:
        return m.group(1).strip() + "\n", "html"
    return text, "txt"


def save_oneshot(label, workload, run_tag, text):
    os.makedirs(ONESHOT_DIR, exist_ok=True)
    body, ext = extract_artifact(text)
    stem = f"{label}-{workload}" if run_tag in ("", "run1") else f"{label}-{workload}-{run_tag}"
    path = os.path.join(ONESHOT_DIR, f"{stem}.{ext}")
    with open(path, "w") as f:
        f.write(body)
    return path


def main():
    ap = argparse.ArgumentParser(
        description="Benchmark a Project Maya server (DeepSeek-V4.1-Flash-1017).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--base", default=os.environ.get("BENCH_BASE")
                    or f"http://127.0.0.1:{os.environ.get('PORT', '18091')}")
    ap.add_argument("--model", default="deepseek-v4.1-flash")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--workload", default="prose", choices=ALL_WORKLOADS)
    ap.add_argument("--isl", type=int, default=8192, help="target prompt tokens (random workload only)")
    ap.add_argument("--osl", type=int, default=None,
                    help="max output tokens (default 1024, or 16384 for a one-shot game)")
    ap.add_argument("--runs", type=int, default=None, help="measured runs (default 3, or 1 for a one-shot)")
    ap.add_argument("--warmup", type=int, default=None, help="unmeasured runs first (default 1, or 0 for a one-shot)")
    ap.add_argument("--thinking", action="store_true", help="ask for thinking mode (default: off)")
    ap.add_argument("--effort", default=None,
                    help="reasoning effort: none|low|high|max, or 1-100 (mapped onto Maya's enum)")
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--ignore-eos", action="store_true",
                    help="Maya's server has no ignore_eos; the run is capped with max_tokens instead "
                         "(and --fixed-len says whether the length really was pinned)")
    ap.add_argument("--fixed-len", action="store_true",
                    help="warn in the JSON when the model stopped by itself, i.e. the output length "
                         "was not pinned and two configs are compared on different amounts of work")
    ap.add_argument("--seed", type=int, default=None, help="sampling seed passed to the server")
    ap.add_argument("--seed-salt", default=None,
                    help="Fixes the prompt seed. Runs that share a salt get IDENTICAL prompts, "
                         "which is required to compare two server configs on the random "
                         "workload -- there the generated text decides both acceptance and which "
                         "experts are touched, so different prompts are different experiments. "
                         "Default: derived from --label.")
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", default=None, help="write the summary JSON here")
    ap.add_argument("--no-save-oneshot", action="store_true",
                    help="do not write results/oneshots/<label>-<workload>.html")
    ap.add_argument("--metrics-endpoint", default="/metrics",
                    help="Maya's metrics endpoint (the engine stats live here)")
    a = ap.parse_args()

    oneshot = a.workload in ONE_SHOTS
    if a.osl is None:
        a.osl = 16384 if oneshot else 1024
    if a.runs is None:
        a.runs = 1 if oneshot else 3
    if a.warmup is None:
        a.warmup = 0 if oneshot else 1
    effort = map_effort(a.effort)

    if a.ignore_eos:
        print("INFO: Maya's server does not support ignore_eos; the run is capped with "
              "max_tokens instead. Read finish_reason: 'length' = the cap was hit, "
              "'stop' = the model ended the answer itself (the length is not pinned).")

    served = get_json(a.base, "/v1/models", a.api_key)["data"][0]["id"]
    if served != a.model:
        print(f"note: server serves '{served}', using that")
        a.model = served
    health = get_json(a.base, "/health", a.api_key)

    print(f"== {a.label}: workload={a.workload} isl={a.isl if a.workload == 'random' else 'n/a'} "
          f"osl={a.osl} runs={a.runs} warmup={a.warmup} thinking={a.thinking} effort={effort} "
          f"engine={health.get('model')} base={a.base}")
    results = []
    warnings = []
    # Seed from the label too: two benches in one server session (e.g. the thinking and
    # non-thinking rows) must not share prompts, or the second is served warm -- both
    # from any prefix cache and from an expert arena the first run already filled.
    salt_src = a.seed_salt if a.seed_salt is not None else a.label
    label_salt = int(hashlib.sha1(salt_src.encode()).hexdigest()[:6], 16) % 100000
    for i in range(a.warmup + a.runs):
        seed = 1000 + i + label_salt          # fresh prompt every run
        if a.workload == "random":
            prompt, n = fit_prompt(a.base, a.model, a.isl, seed, a.api_key, a.thinking)
        elif oneshot:
            # No uniqueness tag: these prompts must stay byte-identical to the
            # ones the routing trace was taken on.
            prompt = WORKLOADS[a.workload]
            n = token_len(a.base, prompt, a.model, a.api_key, a.thinking)
        else:
            # Real prompt; a unique tag keeps a prefix cache from serving run N
            # from run N-1's blocks, which would fake a near-zero TTFT.
            prompt = f"[req {seed}] " + WORKLOADS[a.workload]
            n = token_len(a.base, prompt, a.model, a.api_key, a.thinking)
        r = run_once(a.base, a.model, prompt, a.osl, a.api_key, a.thinking, effort, a.temperature,
                     a.seed, ignore_eos=a.ignore_eos)
        r["prompt_tokens_actual"] = n
        measured = i >= a.warmup
        tag = "warmup" if not measured else f"run{i - a.warmup + 1}"
        # Maya's engine stats live in /metrics, not in the stream: read them after
        # the run, so the snapshot shows the state the run produced.
        stats, raw_metrics = metrics_snapshot(a.base, a.metrics_endpoint, a.api_key)
        r["x_engine_stats"] = {k: stats.get(k) for k in HEADLINE_STATS} if stats else {}
        r["engine_extra"] = {k: v for k, v in (stats or {}).items() if k not in HEADLINE_STATS}
        if oneshot and not a.no_save_oneshot:
            r["artifact"] = save_oneshot(a.label, a.workload, tag, r["_content"] or r["_reasoning"])
        text = r.pop("_content")
        r.pop("_reasoning")
        r["completion_chars"] = len(text)
        st = r["x_engine_stats"]
        if measured and a.fixed_len and r["finish_reason"] not in ("length", None):
            w = (f"run{i - a.warmup + 1}: finish_reason='{r['finish_reason']}' -- the model stopped "
                 f"by itself, the output length is NOT pinned (Maya has no ignore_eos)")
            warnings.append(w)
            print(f"  WARN  {w}")
        print(f"  {tag:7s} isl={n} ttft={r['ttft_ms']:9.1f} ms  tpot={r['tpot_ms']:7.2f} ms  "
              f"decode={r['decode_tok_s']:6.2f} tok/s  out={r['completion_tokens']} ({r['finish_reason']})")
        print(f"          accept_len={st.get('accept_len_mean')}  expert_hit={st.get('expert_hit_rate')}  "
              f"nvme={st.get('nvme_gb')} GB  engram_rows={st.get('engram_rows')}")
        if r["server_timings"].get("prompt_per_second") is not None:
            print(f"          prefill={r['server_timings']['prompt_per_second']} tok/s (server)  "
                  f"engine_decode={r['server_timings'].get('predicted_per_second')} tok/s")
        if "artifact" in r:
            print(f"          wrote {os.path.relpath(r['artifact'], REPO_ROOT)}")
        if measured:
            results.append(r)

    def med(key):
        vals = [x[key] for x in results if x.get(key) is not None]
        return round(statistics.median(vals), 4) if vals else None

    engine_meds = {}
    for k in HEADLINE_STATS:
        vals = [x["x_engine_stats"].get(k) for x in results
                if isinstance(x.get("x_engine_stats"), dict) and x["x_engine_stats"].get(k) is not None]
        engine_meds[k] = round(statistics.median(vals), 4) if vals else None

    summary = {
        "label": a.label, "workload": a.workload, "seed_salt": a.seed_salt,
        "isl": a.isl if a.workload == "random" else None, "osl": a.osl,
        "runs": a.runs, "warmup": a.warmup,
        "thinking": a.thinking, "effort": effort, "temperature": a.temperature,
        "ignore_eos": a.ignore_eos,
        "fixed_len": a.fixed_len,
        "base": a.base, "model": a.model, "health": health,
        "ttft_ms_median": med("ttft_ms"),
        "tpot_ms_median": med("tpot_ms"),
        "decode_tok_s_median": med("decode_tok_s"),
        # The engine's own rates for the run: the prompt read (prefill) and the
        # decode it measured. The wall-clock numbers above are ours.
        "prefill_tok_s_median": round(statistics.median(
            [x["server_timings"]["prompt_per_second"] for x in results
             if x.get("server_timings", {}).get("prompt_per_second") is not None]), 4)
            if any(x.get("server_timings", {}).get("prompt_per_second") is not None for x in results) else None,
        "engine_decode_tok_s_median": round(statistics.median(
            [x["server_timings"]["predicted_per_second"] for x in results
             if x.get("server_timings", {}).get("predicted_per_second") is not None]), 4)
            if any(x.get("server_timings", {}).get("predicted_per_second") is not None for x in results) else None,
        "engine_median": engine_meds,
        "warnings": warnings,
        "metrics_raw": metrics_snapshot(a.base, a.metrics_endpoint, a.api_key)[1],
        "raw": results,
    }
    print(f"  -> MEDIAN  ttft={summary['ttft_ms_median']} ms  tpot={summary['tpot_ms_median']} ms  "
          f"decode={summary['decode_tok_s_median']} tok/s")
    print(f"  -> ENGINE  accept_len={engine_meds['accept_len_mean']}  "
          f"expert_hit={engine_meds['expert_hit_rate']}  nvme={engine_meds['nvme_gb']} GB  "
          f"engram_rows={engine_meds['engram_rows']}")
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"  wrote {a.out}")


if __name__ == "__main__":
    sys.exit(main())
