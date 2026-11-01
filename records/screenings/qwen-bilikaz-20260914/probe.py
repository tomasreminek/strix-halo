"""Read-only GGUF head inspection and 60s production observation. No inference requests."""
import datetime
import json
import subprocess
import time
from pathlib import Path
from gguf import GGUFReader

out = Path(__file__).resolve().parent
start = datetime.datetime.now().astimezone()
report = {'start': start.isoformat(), 'mode': 'passive production observation; NOT controlled A/B', 'heads': [], 'samples': []}
files = list(Path('/mnt/c/AI-Models/Qwen38-Flash-Next-Uncensored-Q4_K_M').glob('*.gguf')) + list(Path('/mnt/c/AI-Models/Qwen38-Flash-Next-MTP').glob('mtp-Qwen3.8-Flash-Next-Q8_0.gguf'))
for path in files:
    reader = GGUFReader(str(path), mode='r')
    for t in reader.tensors:
        if t.name == 'output.weight' or 'head' in t.name or 'output_hc' in t.name:
            report['heads'].append({'file': path.name, 'name': t.name, 'type': t.tensor_type.name, 'shape': t.shape.tolist(), 'bytes': int(t.n_bytes)})
    del reader

def sample():
    vals = {}
    for line in Path('/proc/vmstat').read_text().splitlines():
        key, value = line.split()
        if key.startswith(('compact_', 'pswpin', 'pswpout')):
            vals[key] = int(value)
    return {'time': time.time(), 'compaction_proactiveness': int(Path('/proc/sys/vm/compaction_proactiveness').read_text()), 'counters': vals}

for i in range(13):
    report['samples'].append(sample())
    if i < 12:
        time.sleep(5)
a, b = report['samples'][0], report['samples'][-1]
report['elapsed_seconds'] = b['time'] - a['time']
report['counter_deltas'] = {k: b['counters'][k] - a['counters'][k] for k in a['counters']}
sudo = subprocess.run(['sudo', '-n', 'true'], capture_output=True, text=True)
report['sudo_probe'] = {'exit': sudo.returncode, 'stderr': sudo.stderr.strip()}
log = subprocess.run(['journalctl', '--user', '-u', 'qwen38-orca.service', '--since', start.isoformat(), '--no-pager', '-o', 'cat'], capture_output=True, text=True)
# Publish only engine timing/counter lines, not prompts or generated user content.
selected = [l for l in log.stdout.splitlines() if any(k in l for k in ('print_timing', 'prompt eval time', 'eval time', 'draft acceptance'))]
(out / 'timings.log').write_text('\n'.join(selected) + '\n')
report['timing_lines'] = len(selected)
(out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k != 'samples'}, indent=2))
