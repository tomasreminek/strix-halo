#!/usr/bin/env bash
# Prefill + decode at 32k / 64k / 128k context, 2 repetitions each (the overnight 32k row was noise).
# Each run: -p 2048 (tokens actually prefilled) -n 128 -d <KV depth>
set -uo pipefail
cd "$(dirname "$0")"

R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF
M=models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf
export DS41_ENGRAM_SHARDS="models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf:$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00006-of-00006.gguf"
export LD_LIBRARY_PATH=/mnt/c/AI-Models/unsloth-llama-b10698-mix-rocm-gfx1151:${LD_LIBRARY_PATH:-}

OUT=$HOME/gufo-iq1m-results
CSV=$OUT/depth-sweep.csv
: > "$CSV"; echo "depth,rep,prefill_tps,decode_tps,wall_s" >> "$CSV"

for D in 32768 65536 131072; do
  for REP in 1 2; do
    log="$OUT/depth_${D}_r${REP}.log"
    t0=$(date +%s.%N)
    systemd-run --user --scope --quiet --collect -p MemoryMax=infinity \
      --unit="gufo-depth-$$-$RANDOM" \
      ./build/gufo bench -m "$M" --stream-experts -p 2048 -n 128 -d "$D" \
      > "$log" 2>&1
    t1=$(date +%s.%N)
    wall=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.1f", b-a}')
    pp=$(grep -oE "pp[0-9]+ @ d[0-9]+ *\| *[0-9.]+" "$log" | tail -1 | grep -oE '[0-9.]+$')
    tg=$(grep -oE "tg[0-9]+ @ d[0-9]+ *\| *[0-9.]+" "$log" | tail -1 | grep -oE '[0-9.]+$')
    echo "$D,$REP,${pp:-NA},${tg:-NA},$wall" >> "$CSV"
    echo "[d=$D rep=$REP] prefill=${pp:-NA} tok/s  decode=${tg:-NA} tok/s  wall=${wall}s"
  done
done

echo
echo "=== SOUHRN ==="
python3 - "$CSV" <<'PY'
import csv, sys, statistics
rows = [r for r in csv.DictReader(open(sys.argv[1])) if r["prefill_tps"] != "NA"]
by = {}
for r in rows:
    by.setdefault(int(r["depth"]), []).append((float(r["prefill_tps"]), float(r["decode_tps"])))
print(f"{'depth':>8} {'prefill (min-max)':>24} {'decode (min-max)':>20}")
for d in sorted(by):
    p = [x[0] for x in by[d]]; g = [x[1] for x in by[d]]
    print(f"{d:>8} {min(p):8.2f} - {max(p):8.2f}  (n={len(p)}) {min(g):7.2f} - {max(g):7.2f}")
PY
echo
echo "[$(date +%H:%M:%S)] DEPTH SWEEP HOTOV"
