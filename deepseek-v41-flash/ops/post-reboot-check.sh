#!/usr/bin/env bash
# Post-reboot verification for the GPU-wedge recovery (see strix-halo
# deepseek-v41-flash/MAYA-AMD-RESULTS.md section 5.5).
#
# Checks, in order:
#   1. KFD is openable again (the failure mode was EINVAL on /dev/kfd)
#   2. amdgpu reports a live GPU
#   3. Strata is serving on :18087 with loaded: true
#   4. DSH is serving on :18095
#   5. Hermes gateway is active
#
# Writes a plain-text report. Never starts a second engine, never touches
# the Maya engine, never restarts the gateway.

LOG_DIR="$HOME/.hermes/logs"
LOG="$LOG_DIR/maya-post-reboot.log"
mkdir -p "$LOG_DIR"

say() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >>"$LOG"; }

{
  echo "==============================================================="
  echo "Post-reboot verification   $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "boot_id: $(cat /proc/sys/kernel/random/boot_id 2>/dev/null)"
  echo "==============================================================="

  # --- 1. KFD -------------------------------------------------------------
  say "checking /dev/kfd"
  KFD="BROKEN"
  if python3 - <<'PY' >/dev/null 2>&1
import os
fd = os.open('/dev/kfd', os.O_RDWR)
os.close(fd)
PY
  then
    KFD="OK (O_RDWR opened)"
  else
    KFD="BROKEN (still EINVAL / not openable)"
  fi
  say "  /dev/kfd: $KFD"
  echo "/dev/kfd: $KFD"

  # --- 2. rocminfo (HIP-level proof) -------------------------------------
  ROCMINFO_BIN=""
  for c in /mnt/data/toolchains/strata-rocm-7.14.1-gfx1151/install/bin/rocminfo \
           /opt/rocm/bin/rocminfo "$(command -v rocminfo 2>/dev/null)"; do
    [ -n "$c" ] && [ -x "$c" ] && { ROCMINFO_BIN="$c"; break; }
  done
  ROCMINFO="not found"
  if [ -n "$ROCMINFO_BIN" ]; then
    RINFO="$(timeout 40 "$ROCMINFO_BIN" 2>&1)"
    if printf '%s' "$RINFO" | grep -qi 'gfx1151'; then
      ROCMINFO="OK (gfx1151 agent enumerated)"
    elif printf '%s' "$RINFO" | grep -qi 'error'; then
      ROCMINFO="BROKEN ($(printf '%s' "$RINFO" | grep -i 'error' | head -1 | cut -c1-140))"
    else
      ROCMINFO="UNKNOWN (no gfx1151, no error line)"
    fi
  fi
  say "  rocminfo: $ROCMINFO"
  echo "--- rocminfo ---"
  echo "$ROCMINFO"

  # --- 3. amdgpu ----------------------------------------------------------
  ROCM_SMI=""
  for c in /mnt/data/toolchains/strata-rocm-7.14.1-gfx1151/install/bin/rocm-smi \
           /opt/rocm/bin/rocm-smi "$(command -v rocm-smi 2>/dev/null)"; do
    [ -n "$c" ] && [ -x "$c" ] && { ROCM_SMI="$c"; break; }
  done
  if [ -n "$ROCM_SMI" ]; then
    SMIOUT="$(timeout 25 "$ROCM_SMI" 2>&1 | grep -iE 'GPU\[|card series' | head -4)"
    [ -z "$SMIOUT" ] && SMIOUT="$(timeout 25 "$ROCM_SMI" 2>&1 | head -3)"
  else
    SMIOUT="rocm-smi not found"
  fi
  say "  rocm-smi: $SMIOUT"
  echo "--- rocm-smi ---"
  echo "$SMIOUT"

  # --- 3. Strata ----------------------------------------------------------
  echo "--- Strata :18087 ---"
  MAXWAIT="${MAXWAIT:-90}"
  for i in $(seq 1 "$MAXWAIT"); do
    CODE="$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:18087/health 2>/dev/null)"
    if [ "$CODE" = "200" ]; then
      BODY="$(curl -s -m 5 http://127.0.0.1:18087/health 2>/dev/null | head -c 300)"
      echo "loaded-check: $BODY"
      if printf '%s' "$BODY" | grep -qi 'loaded.*true\|"loaded":true'; then
        say "Strata: loaded: true after ${i}0s"
        echo "RESULT: Strata OK (loaded: true) after $((i*10))s"
        break
      fi
    fi
    [ $((i % 6)) -eq 0 ] && say "waiting for Strata (attempt $i, http=${CODE:-none})"
    sleep 10
  done

  # --- 4. DSH -------------------------------------------------------------
  echo "--- DSH :18095 ---"
  DSHCODE="$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:18095/ 2>/dev/null)"
  say "  DSH http=${DSHCODE:-none}"
  echo "DSH http=${DSHCODE:-none}"

  # --- 5. Hermes ----------------------------------------------------------
  echo "--- services ---"
  for s in hermes-gateway strata-ablit-unsloth dsh-strata-web roots-of-pacha-worker; do
    ST="$(systemctl --user is-active "$s" 2>/dev/null || echo unknown)"
    EN="$(systemctl --user is-enabled "$s" 2>/dev/null || echo unknown)"
    echo "$s: active=$ST enabled=$EN"
    say "  $s: active=$ST enabled=$EN"
  done

  # --- 7. no stale Maya/probe engine --------------------------------------
  echo "--- engine processes ---"
  MP="$(pgrep -fa '[b]uild-hip/maya-ds4|[m]aya-probe' 2>/dev/null | head -5)"
  if [ -z "$MP" ]; then
    MP="none (clean: no Maya/probe instance running)"
  fi
  echo "maya-ds4 procs: $MP"
  say "  maya-ds4 procs: $MP"

  echo "--- GPU reset counter in this boot ---"
  RC="$(journalctl -k --no-pager -b 2>/dev/null | grep -c 'GPU reset begin' 2>/dev/null || echo 0)"
  echo "GPU resets since boot: $RC"
  say "GPU resets since boot: $RC"

  echo "==============================================================="
  echo "done $(date '+%Y-%m-%d %H:%M:%S')"
} >>"$LOG" 2>&1

say "verification finished"
