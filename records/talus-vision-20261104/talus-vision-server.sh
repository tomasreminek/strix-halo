#!/usr/bin/env bash
# Talus engine (fast prefill + MTP) behind Strata's Python serve.server, which adds the
# vision/OCR path (mmproj -> strata-vision -> GENI). talus-server 0.1.3 cannot do images.
set -euo pipefail
CONTROL="$HOME/.local/share/strata/components/control/0.1.56"
cd "$CONTROL"
exec env \
  PYTHONPATH=/mnt/c/ai/rocm-sdk \
  STRATA_PF_FUSED=1 STRATA_PF_GEMM=1 STRATA_HC_UPMIX=1 STRATA_PA_FAST=1 \
  STRATA_HIP_WMMA=1 STRATA_SELECT_WMMA=1 STRATA_HC_Q8=1 \
  STRATA_PF_SWITCH_MIN_T=0 STRATA_PREFILL_STREAM_MIN=128 \
  "$CONTROL/python/bin/python3.12" -m serve.server \
    --engine strata \
    --config "$HOME/.config/talus/run-vision.json" \
    --host 127.0.0.1 --port 18087
