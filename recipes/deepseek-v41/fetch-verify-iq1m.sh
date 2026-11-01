#!/usr/bin/env bash
# Downloads and SHA256-verifies all 5 ISTA IQ1_M shards, then hands control to the benchmark driver.
# On a hash mismatch the shard is deleted and re-downloaded (max 3 attempts). Never benchmarks unverified data.
set -uo pipefail
D=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/ISTA-IQ1M
OUT="$HOME/gufo-iq1m-results"
REPO="https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF/resolve/main"
PREFIX="DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-0000"
mkdir -p "$OUT"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$OUT/fetch.log"; }

declare -A SZ SHA
SZ[1]=5780704;              SHA[1]=3e8ddd11441edd4bc19bacaef5dbe38818af2cbdf0820fb70f1d2d851fcc192a
SZ[2]=39340012896;          SHA[2]=be4ceb1caf1bed28e886860cf6a52adc8f5ca9eb0d2098ade39bb4179d48b323
SZ[3]=38698805888;          SHA[3]=758c66ba65236e8ce0820c21a7b6f9b2947681df8cc509f672a77722e8191b9a
SZ[4]=39707055008;          SHA[4]=04a5bea2b38eb576f49efc19c0a677768d6e2a8ea5772d72fb6cb79e1733a212
SZ[5]=2969539840;           SHA[5]=7c8dbee99890f05dbc420eba6f44393f5228d06248fe61e1ae8ed002449c7549

path_of() { echo "$D/${PREFIX}$1-of-00006.gguf"; }

verify() {
  local i=$1 f; f=$(path_of "$i")
  [ -f "$f" ] || return 1
  [ "$(stat -c %s "$f" 2>/dev/null || echo 0)" -eq "${SZ[$i]}" ] || return 1
  local h; h=$(sha256sum "$f" | cut -d' ' -f1)
  [ "$h" = "${SHA[$i]}" ]
}

fetch() {
  local i=$1 f attempt have h
  f=$(path_of "$i")
  for attempt in 1 2 3; do
    if verify "$i"; then log "shard $i OK (sha256)"; return 0; fi
    have=$(stat -c %s "$f" 2>/dev/null || echo 0)
    if [ "$have" -gt "${SZ[$i]}" ]; then
      log "shard $i pretekl ($have > ${SZ[$i]}) -> mazu"; rm -f "$f"; have=0
    fi
    log "shard $i pokus $attempt: stahuji od $have / ${SZ[$i]}"
    curl -L -C - --retry 30 --retry-delay 5 --retry-all-errors --connect-timeout 30 \
         -sS -o "$f" "$REPO/${PREFIX}$i-of-00006.gguf" >> "$OUT/fetch.log" 2>&1
    sync
    if verify "$i"; then log "shard $i OK po stazeni"; return 0; fi
    h=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1)
    log "shard $i: SHA256 NESEDI (mam ${h:-none}) -> mazu a zacinam od nuly"
    rm -f "$f"
  done
  log "shard $i: 3 pokusy vycerpany, KONCIM"
  return 1
}

log "=== start: stahovani + verifikace 5 shardu ==="
for i in 1 2 3 4 5; do
  fetch "$i" || { log "ABORT: shard $i neoveren, benchmark nespusten"; exit 1; }
done
log "=== vsech 5 shardu SHA256-overeno ==="

# hand control to the benchmark driver (its wait loop passes immediately, the hash check passes)
exec bash "$HOME/Projekty/gufo-ds41/overnight-iq1m.sh"
