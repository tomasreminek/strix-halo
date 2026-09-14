#!/usr/bin/env python3
"""Static compatibility probe for the DeepSeek V4.1 Spark engine on Strix Halo."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
scan_roots = [ROOT / "engine", ROOT / "tools", ROOT / "server", ROOT / "scripts"]
patterns = {
    "direct torch.cuda references": re.compile(r"torch\.cuda"),
    "CUDA graph references": re.compile(r"CUDAGraph|cuda graph|CUDA graph", re.I),
    "NVIDIA architecture target": re.compile(r"sm_121a|sm_121|GB10|CUDA 13"),
    "CUDA device literals": re.compile(r"[\"']cuda[\"']"),
}

hits: dict[str, list[str]] = {name: [] for name in patterns}
for base in scan_roots:
    if not base.exists():
        continue
    for path in sorted(base.rglob("*.py")):
        text = path.read_text(errors="replace")
        rel = path.relative_to(ROOT)
        for name, pattern in patterns.items():
            count = len(pattern.findall(text))
            if count:
                hits[name].append(f"{rel}: {count}")

print("DeepSeek V4.1 Flash / Strix Halo static probe")
print(f"root={ROOT}")
print("target=gfx1151 (AMD ROCm/HIP/Vulkan)")
print("status=CUDA-specific upstream; AMD port required")
for name, rows in hits.items():
    print(f"{name}: {sum(int(row.rsplit(': ', 1)[1]) for row in rows)}")
    for row in rows[:12]:
        print(f"  {row}")
    if len(rows) > 12:
        print(f"  ... {len(rows) - 12} more files")

print("checkpoint_downloaded=no")
print("production_route_changed=no")
