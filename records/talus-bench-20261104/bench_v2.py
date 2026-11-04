#!/usr/bin/env python3
"""bench_v2.py — prefill + decode across context depths, identical methodology for any OpenAI /v1 server.

Per depth D:
  A) cold prefill: unique salt + corpus to ~D tokens, max_tokens=1, non-streaming -> pp_tps = prompt_tokens/wall
  B) decode: same prompt again (prompt cache hit), max_tokens=NPRED, streaming -> tg_tps = completion_tokens/(t_last-t_first)

Usage: bench_v2.py <label> <base_url> [depths]
Writes /home/tomasreminek/.hermes/cache/scratch/bench_<label>.json
"""
import glob, json, sys, time, urllib.request, uuid

LABEL = sys.argv[1]
URL = sys.argv[2].rstrip("/")
DEPTHS = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "2000,8000,32000,65536").split(",")]
NPRED = int(__import__("os").environ.get("NPRED", "256"))
MODEL = __import__("os").environ.get("BENCH_MODEL", "qwen3.8-flash-next-unsloth-ud-iq4_xs")

def corpus():
    fs = sorted(glob.glob("/usr/lib/python3.*/[a-m]*.py"))
    return "\n\n".join(open(f, errors="ignore").read() for f in fs)

TEXT = corpus()

def req(content, max_tokens, stream=False, timeout=1800):
    body = {"model": MODEL, "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens, "temperature": 0}
    if stream:
        body.update({"stream": True, "stream_options": {"include_usage": True}})
    r = urllib.request.Request(URL + "/v1/chat/completions", data=json.dumps(body).encode(),
                               headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
    t0 = time.time()
    if not stream:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            d = json.load(resp)
        return {"usage": d.get("usage", {}), "wall": time.time() - t0}
    first = last = None
    usage = {}
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        for line in resp:
            s = line.decode(errors="ignore").strip()
            if not s.startswith("data:"):
                continue
            p = s[5:].strip()
            if p == "[DONE]":
                break
            try:
                j = json.loads(p)
            except Exception:
                continue
            if j.get("usage"):
                usage = j["usage"]
            for ch in j.get("choices", []):
                dl = ch.get("delta") or {}
                if dl.get("content") or dl.get("reasoning_content"):
                    now = time.time()
                    first = first or now
                    last = now
    return {"usage": usage, "wall": time.time() - t0, "first": first, "last": last, "t_start": t0}

results = {"label": LABEL, "url": URL, "time": time.strftime("%F %T"), "runs": []}
for d in DEPTHS:
    salt = f"[run {uuid.uuid4().hex[:10]}]\n"
    n = int(d * 4.0)
    # calibrate the character count so the prompt lands near the target depth (cheap: cached afterwards)
    for _ in range(3):
        r = req(salt + TEXT[:n] + "\n\nContinue the code above:\n", 1)
        got = r["usage"].get("prompt_tokens", 0)
        if got == 0 or abs(got - d) <= 0.03 * d:
            break
        n = max(200, int(n * d / got))
    body = TEXT[:n] + "\n\nContinue the code above:\n"
    prompt = f"[cold {uuid.uuid4().hex[:12]}]\n" + body   # fresh salt: the calibration probes cannot satisfy this from cache
    cold = req(prompt, 1)
    pt = cold["usage"].get("prompt_tokens", 0)
    pp = round(pt / cold["wall"], 1) if cold["wall"] else None
    warm = req(prompt, NPRED, stream=True)
    ct = warm["usage"].get("completion_tokens", 0)
    ttft = (warm["first"] - warm["wall"] + cold["wall"]) if warm.get("first") else None
    dec = (warm["last"] - warm["first"]) if warm.get("first") and warm.get("last") else None
    tg = round(ct / dec, 2) if dec and dec > 0 else None
    run = {"depth": pt, "pp_tps": pp, "tg_tps": tg, "tg_n": ct, "prefill_s": round(cold["wall"], 2),
           "warm_ttft_ms": int((warm["first"] - warm["t_start"]) * 1000) if warm.get("first") else None}
    print(json.dumps({k: run[k] for k in ("depth", "pp_tps", "tg_tps", "tg_n", "prefill_s")}), flush=True)
    results["runs"].append(run)
json.dump(results, open(f"/home/tomasreminek/.hermes/cache/scratch/bench_{LABEL}.json", "w"), indent=1)
print("saved bench_%s.json" % LABEL)
