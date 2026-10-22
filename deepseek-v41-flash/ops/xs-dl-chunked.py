#!/usr/bin/env python3
"""Maya-XS parallel chunked downloader (resume-safe, SHA256-verified).

Files: peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF @ c273fcbdda76a1db074c2f414cb70edbfca2f2ef
  Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-0000{1..5}-of-00005.gguf
  dspark/dspark-xs2.bin
  dspark/dspark-xs2.json

Design: one global thread pool over byte-range chunks of all files at once.
Completed ranges are persisted per file so a restart resumes instead of re-fetching.
The file is preallocated to its exact size and chunks are written with pwrite() at
their own offset, so a chunk can never corrupt another one.
"""
import hashlib
import json
import os
import pathlib
import sys
import threading
import time
import urllib.error
import urllib.request

REPO = "peasantsmith/DeepSeek-V4.1-Flash-1017-Maya-GGUF"
REV = "c273fcbdda76a1db074c2f414cb70edbfca2f2ef"
BASE = f"https://huggingface.co/{REPO}/resolve/{REV}/"
DEST = pathlib.Path(os.environ.get("XS_DEST", "/mnt/data/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF"))
STATE = pathlib.Path(os.environ.get("XS_STATE", "/home/tomasreminek/.hermes/state/xs-dl"))
LOGDIR = pathlib.Path("/home/tomasreminek/.hermes/logs/xs-dl")
CHUNK = int(os.environ.get("XS_CHUNK", 64 * 1024 * 1024))
WORKERS = int(os.environ.get("XS_WORKERS", 24))

FILES = [
    ("Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00001-of-00005.gguf", 47781530400,
     "a0cb7966afd68bc35c46f78018d1fa1d2e4bcbe3c3baf39f60cd1733ed9ad7e5"),
    ("Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00002-of-00005.gguf", 47775748128,
     "ba5afb43adfc667436ebcfbd82d25411fa2843ee7e1d877290611cd60f93cca1"),
    ("Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00003-of-00005.gguf", 19784230848,
     "1482443bb4957c8d2f005ded365445f98558ff05c50674f9ee9a96ddabc122a4"),
    ("Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00004-of-00005.gguf", 80641295472,
     "0d93315942c523d82f6dbc0a6e0e1751548e309f3963f96b82f92e8f9bc52e36"),
    ("Maya-XS/DeepSeek-V4.1-Flash-1017-Maya-XS-IQ1_S-00005-of-00005.gguf", 80643503412,
     "39bbc8cde8b17604fed9a7ba7fc6bc9c5e72e34733657943ac049b4b9ca2d340"),
    ("dspark/dspark-xs2.bin", 4251725568,
     "8dfe21082a6cb320f334fddb454630c241c6d44e0463eef4f8b0b07334511779"),
    ("dspark/dspark-xs2.json", 99146,
     "56d47ad12d6548a8d3d50a79be96451411f18d5b77064de7b8544bb2da22988f"),
]

lock = threading.Lock()
done_bytes = 0
done_chunks = 0
total_bytes = 0
total_chunks = 0
fds = {}
states = {}


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with lock:
        with open(LOGDIR / "xs-dl-chunked.log", "a") as f:
            f.write(line + "\n")


def norm(ranges):
    """merge [(s,e)] into sorted disjoint list (tolerates list/tuple mixes)"""
    if not ranges:
        return []
    ranges = sorted((int(s), int(e)) for s, e in ranges)
    out = [list(ranges[0])]
    for s, e in ranges[1:]:
        if s <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def gaps(size, have):
    """byte ranges still missing"""
    g, cur = [], 0
    for s, e in have:
        if s > cur:
            g.append((cur, s - 1))
        cur = max(cur, e + 1)
    if cur < size:
        g.append((cur, size - 1))
    return g


def get_fd(rel):
    with lock:
        if rel in fds:
            return fds[rel]
        p = DEST / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(p, os.O_RDWR | os.O_CREAT)
        fds[rel] = fd
        return fd


def fetch(rel, start, end, url, tries=8):
    global done_bytes, done_chunks
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}",
                                                       "User-Agent": "maya-xs-dl"})
            with urllib.request.urlopen(req, timeout=180) as r:
                buf = r.read()
            if len(buf) != end - start + 1:
                raise IOError(f"short read {len(buf)} != {end-start+1}")
            fd = get_fd(rel)
            mv = memoryview(buf)
            pos = 0
            while pos < len(mv):
                pos += os.pwrite(fd, mv[pos:], start + pos)
            with lock:
                states[rel]["ranges"].append((start, end))
                states[rel]["ranges"] = norm(states[rel]["ranges"])
                done_bytes += len(buf)
                done_chunks += 1
            return True
        except Exception as ex:
            log(f"retry {attempt} {rel} {start}-{end}: {type(ex).__name__} {ex}")
            time.sleep(min(5 * attempt, 30))
    return False


def sha256_file(rel):
    h = hashlib.sha256()
    with open(DEST / rel, "rb") as f:
        while True:
            b = f.read(16 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)

    queue = []
    for rel, size, sha in FILES:
        sp = STATE / (rel.replace("/", "_") + ".json")
        p = DEST / rel
        if sp.exists():
            # state is the truth: a chunked run preallocates the file to its full size,
            # so the file size alone says nothing about which bytes are valid
            st = json.loads(sp.read_text())
            have = norm([tuple(x) for x in st.get("ranges", [])])
        else:
            st = {"ranges": [], "size": size, "sha": sha}
            have = []
            # first run: adopt the contiguous prefix an earlier sequential download left
            if p.exists():
                fs = p.stat().st_size
                if 0 < fs < size:
                    have = [(0, fs - 1)]
                    log(f"{rel}: adopting sequential prefix {fs} bytes from disk")
        st["ranges"] = [list(x) for x in have]
        st["size"] = size
        st["sha"] = sha
        states[rel] = st
        sp.write_text(json.dumps(st))
        fd = get_fd(rel)
        try:
            os.ftruncate(fd, size)
        except OSError as ex:
            log(f"{rel}: ftruncate {size} failed: {ex}")
        missing = gaps(size, have)
        nchunks = 0
        for s, e in missing:
            for cs in range(s, e + 1, CHUNK):
                ce = min(cs + CHUNK - 1, e)
                queue.append((rel, cs, ce))
                nchunks += 1
        log(f"{rel}: size={size} have={sum(e-s+1 for s,e in have)} missing_chunks={nchunks}")

    global total_bytes, total_chunks
    total_bytes = sum(f[1] for f in FILES)
    total_chunks = len(queue)
    log(f"=== start: {len(queue)} chunks, {total_bytes/1e9:.1f} GB total, workers={WORKERS} ===")

    import concurrent.futures as cf
    ok = True
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {}
        for rel, s, e in queue:
            url = BASE + rel
            futs[ex.submit(fetch, rel, s, e, url)] = (rel, s, e)
        t0 = time.time()
        last = 0
        while futs:
            done_futs = []
            for f in futs:
                if f.done():
                    done_futs.append(f)
            for f in done_futs:
                rel, s, e = futs.pop(f)
                if not f.result():
                    log(f"FAILED chunk {rel} {s}-{e}")
                    ok = False
            with lock:
                db, dc = done_bytes, done_chunks
            if db - last > 5 * 1024 ** 3 or not futs:
                el = max(time.time() - t0, 1)
                log(f"progress {db/1e9:.1f}/{total_bytes/1e9:.1f} GB "
                    f"({100*db/max(total_bytes,1):.1f}%) chunks {dc}/{total_chunks} "
                    f"rate={db/el/1e6:.1f} MB/s elapsed={el/60:.0f} min")
                last = db
            if futs:
                time.sleep(5)
            for rel, s, e in list(futs.values()):
                pass
            # persist state periodically
            for rel, st in states.items():
                (STATE / (rel.replace("/", "_") + ".json")).write_text(json.dumps(st))

    log("=== verifying SHA256 ===")
    for rel, size, sha in FILES:
        p = DEST / rel
        if not p.exists() or p.stat().st_size != size:
            log(f"FAIL_SIZE {rel} {p.stat().st_size if p.exists() else 'missing'} != {size}")
            ok = False
            continue
        h = sha256_file(rel)
        if h != sha:
            log(f"FAIL_SHA {rel} got={h} want={sha}")
            ok = False
        else:
            log(f"OK {rel} {size} {h}")
    log(f"=== {'ALL OK' if ok else 'FAILURES PRESENT'} ===")
    (LOGDIR / ("xs-dl-FINISHED" if ok else "xs-dl-FAILED")).touch()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
