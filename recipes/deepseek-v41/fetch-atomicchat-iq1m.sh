#!/bin/bash
# Fetch the AtomicChat uncensored IQ1_M backbone (4 shards, 120.72 GB).
#
# This is the abliterated twin of the ISTA IQ1_M we already run: same architecture,
# same size_label (384x212B), same deepseek41.* metadata namespace, and it does NOT
# carry the Engram tables inline — its metadata points at
# DeepSeek-V4.1-Flash-Engram-IQ4_NL.gguf, exactly like ISTA points at its shard 06.
# So the Maya-S Engram drop-in (DS41_ENGRAM_SHARDS) applies unchanged.
#
# Every shard is verified by SHA256 and re-fetched from scratch on mismatch; a
# corrupted partial is never resumed, because curl -C - appending to a bad file is
# what silently shifted shard 2 by 24,735,744 bytes on 2026-10-31.

set -u
DIR=/mnt/c/AI-Models/DeepSeek-V4.1-Flash-1017-GGUF/AtomicChat-IQ1M
BASE=https://huggingface.co/AtomicChat/DeepSeek-V4.1-Flash-1017-Uncensored-GSQ-RCO-GGUF/resolve/main
LOG="$DIR/fetch.log"
mkdir -p "$DIR"

# name:size:sha256 — sizes and hashes from the HF API (blobs=true), 2026-11-01
SHARDS=(
"DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00001-of-00004.gguf:39358830464:6e3f0d5ff53d00428ec32c079db9e8255cb410ccaa435e5342aaa8a47fe1339d"
"DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00002-of-00004.gguf:39176113248:34d68c99fdae9948f9f0af0dafe308e805ce0a78d2c48641b24cc57242fdc0af"
"DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00003-of-00004.gguf:39997334720:fb1dd52e9029400beb3457da7f819bbdd18eafe8a28eb12a8151db391bf0cd1e"
"DeepSeek-V4.1-Flash-1017-GSQ-RCO-IQ1_M-00004-of-00004.gguf:2188841824:25eb979db1aac9da8d9f8603fbc99694e361d2526440df71433f7242e0342e98"
)

say() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

say "=== AtomicChat IQ1_M fetch: ${#SHARDS[@]} shards ==="
df -h /mnt/c | tail -1 | tee -a "$LOG"

for entry in "${SHARDS[@]}"; do
  name="${entry%%:*}"; rest="${entry#*:}"; size="${rest%%:*}"; sha="${rest#*:}"
  out="$DIR/$name"

  if [ -f "$out" ] && [ "$(stat -c%s "$out")" = "$size" ]; then
    if [ "$(sha256sum "$out" | cut -d' ' -f1)" = "$sha" ]; then
      say "SKIP $name — already complete and verified"
      continue
    fi
    say "BAD  $name — right size, wrong hash, deleting"
    rm -f "$out"
  fi

  attempt=1
  while [ "$attempt" -le 3 ]; do
    say "GET  $name (attempt $attempt/3, $((size/1000000000)) GB)"
    rm -f "$out"
    if curl -L --fail --retry 2 --retry-delay 5 -C - -o "$out" "$BASE/$name" >> "$LOG" 2>&1; then
      actual=$(stat -c%s "$out" 2>/dev/null || echo 0)
      if [ "$actual" != "$size" ]; then
        say "SIZE MISMATCH $name: got $actual want $size"
      else
        got=$(sha256sum "$out" | cut -d' ' -f1)
        if [ "$got" = "$sha" ]; then
          say "OK   $name  sha256=$got"
          break
        fi
        say "HASH MISMATCH $name: got $got"
      fi
    else
      say "CURL FAILED $name rc=$?"
    fi
    attempt=$((attempt+1))
    sleep 10
  done

  if [ "$attempt" -gt 3 ]; then
    say "GIVING UP on $name after 3 attempts"
    exit 1
  fi
done

say "=== all shards verified ==="
ls -la "$DIR"/*.gguf | tee -a "$LOG"
sha256sum "$DIR"/*.gguf | tee -a "$LOG"
df -h /mnt/c | tail -1 | tee -a "$LOG"
say "DONE"
