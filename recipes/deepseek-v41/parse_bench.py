#!/usr/bin/env python3
"""Vytahne prefill/decode tok/s z logu `gufo bench`.

Gufo tiskne tabulku:
  | model | size | backend | test | t/s |
  | ...   | ...  | ROCm (HIP) | pp2048 | 1234.56 +/- 12.34 |
  | ...   | ...  | ROCm (HIP) | tg128  | 24.50 +/- 0.40 |
  | ...   | ...  | ROCm (HIP) | tg128 @ d8192 | 23.90 +/- 0.30 |

Pouziti: parse_bench.py <log>  ->  vypise "prefill decode" (nebo NA)
"""
import re
import sys

ROW = re.compile(r"\|\s*(pp|tg)(\d+)(?:\s*@\s*d(\d+))?\s*\|\s*([0-9]+(?:\.[0-9]+)?)")


def parse(path):
    prefill = decode = None
    depth = None
    try:
        text = open(path, "r", errors="replace").read()
    except OSError:
        return None, None, None
    for m in ROW.finditer(text):
        kind, _count, d, value = m.group(1), m.group(2), m.group(3), float(m.group(4))
        if d is not None:
            depth = int(d)
        if kind == "pp":
            prefill = value
        else:
            decode = value
    return prefill, decode, depth


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("NA NA")
        sys.exit(1)
    pf, dc, dep = parse(sys.argv[1])
    print(f"{pf if pf is not None else 'NA'} {dc if dc is not None else 'NA'}")
