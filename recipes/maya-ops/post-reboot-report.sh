#!/usr/bin/env bash
# Post-reboot GPU recovery report (cron -> Telegram).
#
# Contract with the caller:
#   * prints NOTHING until the post-reboot verification has completed for a
#     boot that is NEWER than the boot recorded in $STATE/pre-boot-id
#   * prints the report exactly once (marker file $STATE/reported)
#   * prints nothing on every later tick
#
# If the reboot never happened, or the verification never completed, it prints
# a single "verification did not complete" notice once $STATE/deadline passes.
#
# Read-only: it never starts an engine, never restarts the gateway, never
# touches the Maya binary.

LOG="/home/tomasreminek/.hermes/logs/maya-post-reboot.log"
STATE="/home/tomasreminek/.hermes/state/maya-post-reboot"
mkdir -p "$STATE"

PRE_FILE="$STATE/pre-boot-id"
MARKER="$STATE/reported"
DEADLINE_MARKER="$STATE/deadline-reported"
DEADLINE_FILE="$STATE/deadline"

# --- first run: remember the boot we are currently in -----------------------
if [ ! -f "$PRE_FILE" ]; then
  cat /proc/sys/kernel/random/boot_id >"$PRE_FILE" 2>/dev/null
  exit 0
fi
PRE_BOOT_ID="$(cat "$PRE_FILE" 2>/dev/null)"

# --- already reported? -----------------------------------------------------
[ -f "$MARKER" ] && exit 0

# Miss notice. NOTE: it must NOT touch $MARKER -- that marker means "the real
# report was delivered". Setting it here would permanently suppress a report
# that arrives after a late reboot.
report_miss() {
  [ -f "$DEADLINE_MARKER" ] && return 0
  if [ -f "$DEADLINE_FILE" ] && [ "$(date +%s)" -gt "$(cat "$DEADLINE_FILE")" ]; then
    echo "=== Post-reboot GPU recovery ==="
    echo "VERDICT: $1"
    echo "$2"
    touch "$DEADLINE_MARKER"
  fi
}

if [ ! -f "$LOG" ]; then
  report_miss "the post-reboot verification never ran (no $LOG)." \
              "The reboot may not have happened, or the timer did not fire."
  exit 0
fi

# --- find the newest completed verification block for a NEW boot ------------
# A block looks like:
#   ===============================================================
#   Post-reboot verification   <ts>
#   boot_id: <uuid>
#   ===============================================================
#   ...
#   done <ts>
# The checker appends blocks; we take the LAST complete block and check its
# boot_id against the pre-reboot one.
BLOCK="$(awk '
  /^Post-reboot verification/ { buf=""; cap=1 }
  cap { buf = buf $0 "\n" }
  /^done / { if (cap) { last = buf; cap = 0 } }
  END { printf "%s", last }
' "$LOG")"

if [ -z "$BLOCK" ]; then
  report_miss "the post-reboot verification has not completed yet." \
              "Last 20 log lines:
$(tail -20 "$LOG" 2>/dev/null)"
  exit 0
fi

NEW_BOOT_ID="$(printf '%s' "$BLOCK" | grep -m1 '^boot_id:' | sed 's/^boot_id:[[:space:]]*//')"
if [ -z "$NEW_BOOT_ID" ] || [ "$NEW_BOOT_ID" = "$PRE_BOOT_ID" ]; then
  # still the old boot -> the reboot has not happened (or the checker has not
  # run for the new boot yet)
  report_miss "no verification block for a new boot id (pre=$PRE_BOOT_ID, last=${NEW_BOOT_ID:-none})." \
              "The reboot most likely did not happen."
  exit 0
fi

# --- we have a real post-reboot result -------------------------------------
strip() { sed 's/^ *//; s/^[0-9][0-9-]* [0-9:]*  //'; }
KFD="$(printf '%s' "$BLOCK" | grep -m1 '/dev/kfd:' | strip)"
ROCMINFO="$(printf '%s' "$BLOCK" | grep -m1 'rocminfo:' | strip)"
RESETS="$(printf '%s' "$BLOCK" | grep -m1 'GPU resets since boot:' | strip)"
STRATA_RES="$(printf '%s' "$BLOCK" | grep -m1 'RESULT: Strata' | sed 's/^ *//')"
STRATA_ACT="$(printf '%s' "$BLOCK" | grep -m1 'strata-ablit-unsloth:' | sed 's/^ *//; s/^[0-9-]* [0-9:]*  //')"
DSH="$(printf '%s' "$BLOCK" | grep -m1 'DSH http=' | sed 's/^ *//; s/^[0-9-]* [0-9:]*  //')"
HERMES="$(printf '%s' "$BLOCK" | grep -m1 'hermes-gateway:' | strip)"
MAYA_PROCS="$(printf '%s' "$BLOCK" | grep -m1 'maya-ds4 procs:' | strip)"
ROCM="$(printf '%s' "$BLOCK" | grep -m1 'rocm-smi:' | sed 's/^ *//; s/^[0-9-]* [0-9:]*  //' | cut -c1-160)"

echo "=== Post-reboot GPU recovery (boot $NEW_BOOT_ID) ==="
echo "KFD:        $KFD"
echo "rocminfo:   $ROCMINFO"
echo "GPU resets: $RESETS (in this boot)"
echo "rocm-smi:   $ROCM"
echo "Strata:     $STRATA_ACT"
echo "  ${STRATA_RES:-Strata did NOT report loaded:true}"
echo "DSH:        $DSH"
echo "Hermes:     $HERMES"
echo "Maya procs: $MAYA_PROCS"
echo ""

if printf '%s' "$KFD" | grep -q 'OK' && printf '%s' "$ROCMINFO" | grep -q 'OK'; then
  echo "VERDICT: GPU/KFD recovered after the clean reboot."
  echo "Next step: re-run the Maya sweep (v04+ variants) and then restore Strata."
else
  echo "VERDICT: GPU/KFD still broken AFTER a clean reboot."
  echo "That means the wedge is not a recoverable driver-state issue."
  echo "Next step: full power cycle (shutdown, unplug mains, boot) and re-check."
fi

if printf '%s' "$STRATA_RES" | grep -qi 'loaded: true'; then
  echo "Strata is back on :18087 with loaded: true."
else
  echo "Strata is NOT serving loaded:true -- production is still degraded."
fi

touch "$MARKER"
