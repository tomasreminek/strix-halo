#!/usr/bin/env bash
# Gufo benchmark on the ISTA IQ1_M backbone + Maya-S Engram (Q6_K, 2 tables).
# Usage: [STREAM=0|1] ./run-gufo-iq1m.sh <prompt_tokens> <gen_tokens> <depth> [extra args]
#   STREAM=1 (default) -> --stream-experts (stream experts from disk)
#   STREAM=0           -> resident experts (the config the fork author measured 1228/24.5 on)
set -uo pipefail
cd "$(dirname "$0")"

R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF
M=models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf

# Engram = Maya-S shards 5+6 (blk.1 / blk.14). Rows match ISTA (768022850).
# The first path is a symlink in models/ista-iq1m so the backbone list filter drops the 6th shard.
export DS41_ENGRAM_SHARDS="models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf:$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00006-of-00006.gguf"
export LD_LIBRARY_PATH=/mnt/c/AI-Models/unsloth-llama-b10698-mix-rocm-gfx1151:${LD_LIBRARY_PATH:-}

# The Hermes gateway runs in a cgroup with MemoryMax=24G; gufo sees only 4-19 GiB
# of free memory, the expert cache stays at zero and decode collapses to ~5.7 t/s.
# A dedicated systemd scope (MemoryMax=infinity) bypasses that cap.
RUNNER=()
if [ "${NO_SCOPE:-0}" != "1" ] && command -v systemd-run >/dev/null 2>&1; then
  RUNNER=(systemd-run --user --scope --quiet --collect -p MemoryMax=infinity
          --unit="gufo-bench-$$-$RANDOM")
fi

P=${1:-2048}; N=${2:-128}; D=${3:-0}
shift 3 2>/dev/null || true

EXTRA=()
[ "${STREAM:-1}" = "1" ] && EXTRA+=(--stream-experts)

exec "${RUNNER[@]}" ./build/gufo bench -m "$M" "${EXTRA[@]}" -p "$P" -n "$N" -d "$D" -v "$@"
