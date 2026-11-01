#!/usr/bin/env bash
# Overnight: waits for the IQ1_M shards to finish, then runs the benchmark matrix.
# Results: ~/gufo-iq1m-results/ (logs + results.csv + summary.txt)
set -uo pipefail
cd "$(dirname "$0")"
OUT="$HOME/gufo-iq1m-results"
mkdir -p "$OUT"
CSV="$OUT/results.csv"
D=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/ISTA-IQ1M

log() { echo "[$(date '+%F %T')] $*" | tee -a "$OUT/driver.log"; }

# ---------- 1) wait for the shards ----------
declare -A SZ=(
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00002-of-00006.gguf"]=39340012896
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00003-of-00006.gguf"]=38698805888
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00004-of-00006.gguf"]=39707055008
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00005-of-00006.gguf"]=2969539840
)
DEADLINE=$(( $(date +%s) + 9*3600 ))
while :; do
  ready=1; status=""
  for f in "${!SZ[@]}"; do
    have=$(stat -c %s "$D/$f" 2>/dev/null || echo 0)
    status+="$f=$have/${SZ[$f]} "
    [ "$have" -eq "${SZ[$f]}" ] || ready=0
  done
  if [ $ready -eq 1 ]; then log "vsechny shardy kompletni"; break; fi
  if [ "$(date +%s)" -gt "$DEADLINE" ]; then
    log "TIMEOUT cekani na shardy: $status"; log "koncim, benchmark nespusten"; exit 1
  fi
  log "cekam: $status"
  sleep 120
done
sync; sleep 3

# ---------- 1b) SHA256 verification against HF (size alone is not enough) ----------
declare -A SHA=(
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf"]=3e8ddd11441edd4bc19bacaef5dbe38818af2cbdf0820fb70f1d2d851fcc192a
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00002-of-00006.gguf"]=be4ceb1caf1bed28e886860cf6a52adc8f5ca9eb0d2098ade39bb4179d48b323
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00003-of-00006.gguf"]=758c66ba65236e8ce0820c21a7b6f9b2947681df8cc509f672a77722e8191b9a
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00004-of-00006.gguf"]=04a5bea2b38eb576f49efc19c0a677768d6e2a8ea5772d72fb6cb79e1733a212
  ["DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00005-of-00006.gguf"]=7c8dbee99890f05dbc420eba6f44393f5228d06248fe61e1ae8ed002449c7549
)
log "verifikuji SHA256 vsech shardu"
bad=0
for f in "${!SHA[@]}"; do
  h=$(sha256sum "$D/$f" | cut -d' ' -f1)
  if [ "$h" = "${SHA[$f]}" ]; then
    log "  OK   $f"
  else
    log "  BAD  $f (mam $h)"
    bad=1
  fi
done
if [ $bad -ne 0 ]; then
  log "ABORT: poskozena data, benchmark nespusten (spust fetch-verify-iq1m.sh)"
  exit 2
fi
log "vsechny shardy verifikovany, jdu benchmarkovat"

# ---------- 2) benchmark matrix ----------
echo "config,depth,prompt,gen,prefill_tok_s,decode_tok_s,note" > "$CSV"

run() { # nazev depth p n [extra args...]
  local name=$1 depth=$2 p=$3 n=$4; shift 4
  local logf="$OUT/${name}_d${depth}.log"
  log "START $name depth=$depth p=$p n=$n extra=[$*]"
  local t0=$(date +%s)
  if STREAM=$STREAM_VAL timeout "${RUNTIMEOUT:-3600}" ./run-gufo-iq1m.sh "$p" "$n" "$depth" "$@" > "$logf" 2>&1; then
    local dt=$(( $(date +%s) - t0 ))
    local pf dc
    read -r pf dc < <(python3 ./parse_bench.py "$logf")
    if [ "${pf:-NA}" = "NA" ] || [ "${dc:-NA}" = "NA" ]; then
      log "VAROVANI: parser nenasel pp/tg radek v $logf, zkontroluj log"
    fi
    echo "$name,$depth,$p,$n,${pf:-NA},${dc:-NA},${dt}s" >> "$CSV"
    log "DONE  $name depth=$depth prefill=${pf:-NA} decode=${dc:-NA} (${dt}s)"
  else
    local rc=$?
    echo "$name,$depth,$p,$n,FAIL,FAIL,rc=$rc" >> "$CSV"
    log "FAIL  $name depth=$depth rc=$rc -- posledni radky:"
    tail -6 "$logf" | sed 's/^/    /' | tee -a "$OUT/driver.log"
  fi
}

# 0) smoke test: load the model + 8 tokens. If the load or the Engram drop-in is broken,
#    we find out in 5 minutes instead of after two hours of failed runs.
STREAM_VAL=1 RUNTIMEOUT=300 run smoke 0 64 8
if grep -q '^smoke,0,64,8,FAIL' "$CSV"; then
  log "ABORT: smoke test selhal (load modelu / engram drop-in), matrix nespustena"
  { echo "=== SMOKE FAIL ==="; tail -40 "$OUT/smoke_d0.log"; } > "$OUT/summary.txt"
  exit 3
fi
log "smoke OK, poustim plnou matrix"

# 0b) QA gate: the model must generate coherent text (greedy 17*23 = 391).
#     A fast, broken model looks great in a table - tok/s on its own proves nothing.
if ! ./quality-gate.sh; then
  log "ABORT: quality gate selhal (engram drop-in generuje nesmysly), matrix nespustena"
  { echo "=== QUALITY GATE FAIL ==="; tail -60 "$OUT/quality.txt"; } >> "$OUT/summary.txt"
  exit 4
fi
log "quality gate OK (model generuje souradny text)"

# 1) stream = the real path (model 120.7 GB > 111 GB available, resident does not fit)
STREAM_VAL=1 run stream    0 2048 128
STREAM_VAL=1 run stream 8192 2048 128
STREAM_VAL=1 run stream 32768 2048 128
STREAM_VAL=1 run stream 131072 2048 128
# 2) expert cache effect (author: 752/462/384 tok/s at 64/32/16G)
STREAM_VAL=1 run cache64G    0 2048 128 --expert-cache-bytes 64G
STREAM_VAL=1 run cache32G    0 2048 128 --expert-cache-bytes 32G
STREAM_VAL=1 run cache16G    0 2048 128 --expert-cache-bytes 16G
# 3) resident (author's config: 1228/24.5) -- a 120.7 GB model, OOM expected; short timeout
STREAM_VAL=0 RUNTIMEOUT=900 run resident 0 2048 128

log "MATRIX HOTOVA"
{ echo "=== Gufo IQ1_M + Maya-S Engram (Q6_K) ==="; echo "datum: $(date '+%F %T')"; echo
  column -s, -t "$CSV"
  echo; echo "=== QA: kvalita generovani (greedy, seed 42) ==="
  grep -E '^################|^VYSLEDEK|^EXPECT' "$OUT/quality.txt"; } > "$OUT/summary.txt"
cat "$OUT/summary.txt" | tee -a "$OUT/driver.log"
