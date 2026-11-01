#!/usr/bin/env bash
# Precise decode tok/s measurement by the difference method:
#   t(n=192) - t(n=64) = time for 128 tokens  ->  decode tok/s = 128 / delta
# This cancels model load (~6.5 s) and prefill. Measured 2x2 (novel/copy x 64/192).
set -uo pipefail
cd "$(dirname "$0")"

R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF
M=models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf
export DS41_ENGRAM_SHARDS="models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf:$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00006-of-00006.gguf"
export LD_LIBRARY_PATH=/mnt/c/AI-Models/unsloth-llama-b10698-mix-rocm-gfx1151:${LD_LIBRARY_PATH:-}

OUT=$HOME/gufo-iq1m-results
CSV=$OUT/speed-delta.csv
: > "$CSV"; echo "arm,n,seconds" >> "$CSV"

# The Hermes gateway cgroup has MemoryMax=24G -> without its own scope gufo sees ~4 GiB,
# the expert cache stays empty and decode collapses to ~5.7 t/s. Always use a scope.
RUNNER=()
if [ "${NO_SCOPE:-0}" != "1" ] && command -v systemd-run >/dev/null 2>&1; then
  RUNNER=(systemd-run --user --scope --quiet --collect -p MemoryMax=infinity
          --unit="gufo-delta-$$-$RANDOM")
fi

COPYDOC=$(cat <<'EOF'
[server]
listen = 0.0.0.0:8080
workers = 8
timeout_seconds = 120
keepalive_seconds = 65
max_request_bytes = 104857600
log_level = info
log_target = /var/log/service/app.log
metrics_enabled = true
metrics_path = /metrics
tls_enabled = false
tls_cert = /etc/service/tls/cert.pem
tls_key = /etc/service/tls/key.pem
shutdown_grace_seconds = 30
health_path = /healthz
readiness_path = /readyz
queue_depth = 4096
retry_attempts = 3
retry_backoff_ms = 250
circuit_breaker_threshold = 50
circuit_breaker_window_seconds = 60

[database]
host = db.internal
port = 5432
name = production
pool_min = 4
pool_max = 32
idle_timeout_seconds = 300
statement_timeout_ms = 15000
ssl_mode = require
migration_on_start = false

[cache]
backend = redis
host = cache.internal
port = 6379
ttl_seconds = 600
max_memory_mb = 2048
eviction = allkeys-lru

[limits]
rate_limit_per_second = 200
burst = 400
concurrent_uploads = 16
max_upload_bytes = 52428800

[features]
enable_search = true
enable_export = true
enable_webhooks = false
experimental_streaming = false
EOF
)

NOVEL="Write a detailed technical explanation of how a B-tree index works in a relational database, covering node splitting, fanout, page layout, write amplification and the difference between clustered and non-clustered indexes. Be thorough and specific."
COPY="Here is a config file. Output it again verbatim, but change workers from 8 to 16. Output only the file contents, nothing else.

$COPYDOC"

run_one () {
  local arm="$1" n="$2" prompt="$3"
  local log="$OUT/delta_${arm}_${n}.log"
  local t0 t1 dt
  t0=$(date +%s.%N)
  timeout 900 "${RUNNER[@]}" ./build/gufo prompt -m "$M" --stream-experts \
    -p "$prompt" -n "$n" -t 0 -s 42 --think off --no-display-prompt \
    > "$log" 2>&1
  local rc=$?
  t1=$(date +%s.%N)
  dt=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')
  echo "$arm,$n,$dt" >> "$CSV"
  local lk
  lk=$(grep -oE 'lookup_copied=[0-9]+ lookup_accepted=[0-9]+' "$log" | tail -1)
  local cache
  cache=$(grep -oE '[0-9.]+ MiB read/token, [0-9.]+ ms host wait/token' "$log" | tail -1)
  echo "[$arm n=$n] rc=$rc  ${dt}s  ${lk:-lookup=0}  ${cache:-}"
}

echo "=== COLD-ish prvni beh (zahrati) ==="
run_one novel 64 "$NOVEL"

echo "=== MERENI ==="
run_one novel 64  "$NOVEL"
run_one novel 192 "$NOVEL"
run_one copy  64  "$COPY"
run_one copy  192 "$COPY"

echo
echo "=== VYSLEDEK ==="
python3 - "$CSV" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
d = {}
for r in rows:
    d[(r["arm"], int(r["n"]))] = float(r["seconds"])
for arm in ("novel", "copy"):
    try:
        a, b = d[(arm, 64)], d[(arm, 192)]
    except KeyError:
        print(f"{arm:6s} NEMERENO"); continue
    delta = b - a
    tps = 128.0 / delta if delta > 0 else 0.0
    print(f"{arm:6s} t64={a:6.2f}s  t192={b:6.2f}s  delta={delta:6.2f}s  ->  {tps:6.2f} tok/s decode")
PY
