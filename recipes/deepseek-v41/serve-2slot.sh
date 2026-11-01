#!/usr/bin/env bash
# Two-slot server test: -j 2 (2 preallocated sessions), -c 65536 (64k per slot).
# Port 18092. Runs in its own systemd scope (otherwise the 24 GiB cgroup eats it).
set -uo pipefail
cd "$(dirname "$0")"

R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF
M=models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf
export DS41_ENGRAM_SHARDS="models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf:$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00006-of-00006.gguf"
export LD_LIBRARY_PATH=/mnt/c/AI-Models/unsloth-llama-b10698-mix-rocm-gfx1151:${LD_LIBRARY_PATH:-}

exec systemd-run --user --scope --quiet --collect -p MemoryMax=infinity \
  --unit="gufo-serve-test" \
  ./build/gufo serve llm -m "$M" --stream-experts \
  -j 2 -c 65536 -i 127.0.0.1 -p 18092
