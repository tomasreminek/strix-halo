# `ops/` — operational scripts used for the Maya campaign

Snapshot of the scripts that were actually run on this box, copied on
2026-10-22 so the procedure is reproducible without the live home
directory. These are **copies for the record**, not the live versions — the
running copies live in `~/.local/bin/`, `~/.hermes/scripts/` and
`~/.config/systemd/user/`.

| File here | Live path | What it does |
|---|---|---|
| `post-reboot-check.sh` | `~/.local/bin/maya-post-reboot-check.sh` | **Read-only** post-reboot health check: KFD/GPU, Strata `:18087`, DSH `:18095`, Hermes gateway. Writes only to `~/.hermes/logs/`. Touches nothing that is running. |
| `post-reboot-report.sh` | `~/.hermes/scripts/maya-post-reboot-report.sh` | Report runner for the watchdog. Keeps `$STATE/reported` (the main marker) separate from `$STATE/deadline-reported` so a deadline hit never sets the main marker. |
| `maya-post-reboot-check.service` | `~/.config/systemd/user/maya-post-reboot-check.service` | Oneshot unit. `TimeoutStartSec=1200`, sandboxed, `ReadWritePaths=%h/.hermes/logs`. |
| `maya-post-reboot-check.timer` | `~/.config/systemd/user/maya-post-reboot-check.timer` | `OnBootSec=120s`, `WantedBy=timers.target`. |
| `xs-dl-chunked.py` | `~/.local/bin/xs-dl-chunked.py` | Chunked range-resumable downloader (64 MB chunks, global worker pool, `pwrite()` at explicit offsets, per-range state persisted in `~/.hermes/state/xs-dl/`). Used for the Maya-XS shards. |
| `maya-xs-download.service` | `~/.config/systemd/user/maya-xs-download.service` | The unit that runs the downloader. `XS_DEST`, `XS_STATE`, `XS_CHUNK`, `XS_WORKERS` are set via `Environment=`. |

## Rules these scripts encode

- **Never run two writers on the same file.** The old `xs-download.sh` and
  `xs-dl-chunked.py` write to the same targets and must never run at the
  same time.
- **Only one Maya engine at a time.** A second instance is a bug, not a
  fallback.
- **Every environment variable goes through `Environment=` /
  `--setenv=`.** Exported variables are not inherited by `systemd-run`.
- **Every transient unit needs a unique name** and an explicit cgroup
  limit. `systemd-run --user --pty` does not work here
  (`Failed to fork/exec: Invalid argument`) — long processes go in without
  `--pty`.
- **The page cache may only be dropped while the engine is stopped**
  (`maya-drop-cache.py` uses `POSIX_FADV_DONTNEED`).
- **No automatic Strata restore during the Maya tests.** Strata with an
  expert cache must not run concurrently with Maya. It is restored
  deliberately, after the Maya tests are done.
- **`systemctl reboot` is on the hardline blocklist.** The host reboot is a
  human action; the agent must not run it and must not look for a way
  around the block.
