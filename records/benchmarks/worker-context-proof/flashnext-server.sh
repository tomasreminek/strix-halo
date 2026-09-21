#!/usr/bin/env bash
# Qwen3.8-Flash-Next via halogen-flash-server docker container (:18081).
# Measured winner 2026-09-16: MTP decode 44.66 t/s short serving (see
# ~/Projekty/strix-halo/docs/qwen38-halogen.md). Weights on /mnt/c, hash-verified
# per DOWNLOAD_PROVENANCE.json / EXTRAS_PROVENANCE.json.
# One heavy GPU workload: stop other llama/GLM/Comfy units before start.
set -euo pipefail

NAME=halogen-qwen38
IMAGE=ghcr.io/peonist-ai/halogen-flash-server:0.11.0
HOST_API=18081            # host port (container API = 8731)
MODEL_DIR=/mnt/c/AI-Models/Halogen-Qwen38-Flash-Next

case "${1:-up}" in
  up)
    docker rm -f "$NAME" 2>/dev/null || true
    VIDEO_GID="$(getent group video | cut -d: -f3)"
    RENDER_GID="$(getent group render | cut -d: -f3)"
    exec docker run --rm --name "$NAME" \
      -p "127.0.0.1:${HOST_API}:8731" \
      --device /dev/kfd --device /dev/dri \
      --group-add "$VIDEO_GID" --group-add "$RENDER_GID" \
      --ipc=host --ulimit memlock=-1:-1 \
      -e HALOGEN_CTX=65536 \
      -e HALOGEN_KV_POOL_POSITIONS=65536 \
      -e HALOGEN_KV_SLOTS=1 \
      -e HALOGEN_MAX_TOK=8192 \
      -e HALOGEN_FLASH_PIN_TRUNK=1 \
      -e HALOGEN_ENGINE_WATCHDOG_S=0 \
      -e HALOGEN_VISION_TOWER=1 \
      -e HALOGEN_PROMPT_CACHE=2 \
      -e HALOGEN_VERBOSE=1 \
      -e HALOGEN_CK_OVERLAY=/ablit/qwen38-flash-next-w4b.overlay.hgn \
      -v /mnt/c/AI-Models/halogen-flash-next-ablit:/ablit:ro \
      -v "$MODEL_DIR:/models:ro" \
      "$IMAGE" all
    ;;
  down)
    docker rm -f "$NAME" 2>/dev/null || true
    ;;
  *)
    echo "usage: $0 up|down" >&2
    exit 2
    ;;
esac
