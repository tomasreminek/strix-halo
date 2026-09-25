#!/usr/bin/env python3
"""Rebuild synthetic request text for the matched Flash-Next marker tests.

Run with 5000, 33000, or 67500; compare the resulting body against the
corresponding response/summary in this directory. Server-side templates add
model-specific token overhead; use each API's actual usage.prompt_tokens.
"""
import hashlib
import json
import random
import sys

n = int(sys.argv[1])
random.seed(938)
markers = ['START=amber-violet-731', 'MIDDLE=birch-cobalt-482', 'END=cedar-silver-956']
lines = [
    'Record %05d: %s; a quiet bridge crosses a valley with lanterns and rain.\n'
    % (i, ''.join(random.choices('abcdefghjkmnpqrstuvwxyz', k=30)))
    for i in range(3000)
]
chunk = ''.join(lines)
text = (chunk * ((n * 5 // len(chunk)) + 1))[:n * 5]
third = len(text) // 3
text = markers[0] + '\n' + text[:third] + markers[1] + '\n' + text[third:2 * third] + markers[2] + '\n' + text[2 * third:]
prompt = (
    'Read this archival text. The three exact marker values are embedded near '
    'beginning, middle and end. First report all three exactly, then write at '
    'least 300 visible tokens of original prose about a bridge, lanterns and rain. '
    'Do not copy the archive lines.\n' + text
)
print(json.dumps({'n': n, 'corpus_sha256': hashlib.sha256(text.encode()).hexdigest(), 'prompt': prompt}, ensure_ascii=False))
