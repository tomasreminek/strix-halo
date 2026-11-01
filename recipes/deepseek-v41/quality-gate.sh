#!/usr/bin/env bash
# QA gate: verifies the model generates COHERENT text after the Engram drop-in, not just fast tokens.
# Greedy decoding (-t 0), fixed seed -> deterministic. Answers are checked with grep.
# Output: ~/gufo-iq1m-results/quality.txt   Exit: 0 = passed, 1 = failed
set -uo pipefail
cd "$(dirname "$0")"

R=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF
M=models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00006.gguf
export DS41_ENGRAM_SHARDS="models/ista-iq1m/DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00006-of-00006.gguf:$R/Maya-S/DeepSeek-V4.1-Flash-1017-Maya-S-IQ2_XXS-00006-of-00006.gguf"
export LD_LIBRARY_PATH=/mnt/c/AI-Models/unsloth-llama-b10698-mix-rocm-gfx1151:${LD_LIBRARY_PATH:-}
Q="$HOME/gufo-iq1m-results/quality.txt"
: > "$Q"

# The Hermes gateway runs in a cgroup with MemoryMax=24G; gufo sees only 4-19 GiB
# of free memory there. A dedicated systemd scope bypasses that cap (see run-gufo-iq1m.sh).
RUNNER=()
if [ "${NO_SCOPE:-0}" != "1" ] && command -v systemd-run >/dev/null 2>&1; then
  RUNNER=(systemd-run --user --scope --quiet --collect -p MemoryMax=infinity
          --unit="gufo-qa-$$-$RANDOM")
fi

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fails=0
ask() { # nazev prompt n vzor -- kazda odpoved do vlastniho souboru, grepuje se jen odpoved
  local name=$1 p=$2 n=$3 pat=$4 ans="$TMP/$1.ans"
  timeout 900 "${RUNNER[@]}" ./build/gufo prompt -m "$M" --stream-experts \
      -p "$p" -n "$n" -t 0 -s 42 --think off --no-display-prompt > "$ans" 2>&1
  local rc=$? verdict=PASS
  grep -qiE "$pat" "$ans" || verdict=FAIL
  [ "$verdict" = FAIL ] && fails=$((fails+1))
  {
    echo "################ $name  [$verdict]"
    echo "PROMPT: $p"
    echo "EXPECT: $pat   (rc=$rc)"
    echo "---- odpoved ----"
    cat "$ans"
    echo "-----------------"
    echo
  } >> "$Q"
}
ask "matematika" "What is 17*23? Answer with just the number." 96 '\b391\b'
ask "kod"        "Write a Python expression that reverses the string s." 96 '\[::-1\]|reversed'
ask "cestina"    "Jake je hlavni mesto Francie? Odpovez jednim slovem." 48 'Pa[rř][ií][zž]|Paris'

# Hard threshold: at least 2 of 3 must pass. One flaky prompt must not kill the whole night,
# but 0-1 of 3 = total nonsense = broken Engram drop-in -> abort.
echo "=== QUALITY GATE: $fails selhani ze 3 ===" >> "$Q"
if [ "$fails" -le 1 ]; then
  echo "VYSLEDEK: PASS ($((3-fails))/3)" >> "$Q"; exit 0
fi
echo "VYSLEDEK: FAIL ($((3-fails))/3)" >> "$Q"; exit 1
