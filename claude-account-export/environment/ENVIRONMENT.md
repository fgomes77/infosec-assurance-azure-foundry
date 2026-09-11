# Session Container Environment Manifest

Snapshot of the Claude Code remote execution container this export was produced
in, recorded 2026-09-11. The base OS image is Anthropic-provisioned and
reproducible — it is documented here rather than copied, because the operating
system tree is not user data and re-materialises identically in every session.

## Filesystem root layout

| Path | Contents | In this backup? |
|---|---|---|
| `/home/user/<repo>` | The cloned repository (working directory) | Is the repository itself |
| `/mnt/skills` | Anthropic built-in skills (8 public + 32 examples) | Yes — `platform-skills/` |
| `/mnt/attach`, `/mnt/user-data` | Empty session mount points | Nothing to copy |
| `/root/.claude` | Agent config: account skill sync, session hooks, launcher settings | Skills yes (`skills/`); hooks and settings are harness-provisioned per container and blocked from export as sensitive-source — they regenerate automatically |
| `/root/.ccr` | Network proxy CA bundle and credentials | Never exported (credentials) |
| `/tmp` (scratchpad) | Session-temporary files (e.g. the skill upload zips) | Ephemeral by design |
| `/opt` | Pre-installed toolchains (see below) | Documented only |
| `/container_info.json` | Container name stamp | Infrastructure metadata; blocked from export as sensitive-source |
| `/usr`, `/etc`, `/var`, `/boot`, `/srv`, `/media`, `/run` | Base Ubuntu OS image | Reproducible; documented only |
| `/proc`, `/sys`, `/dev` | Virtual kernel filesystems | Not copyable |

## System

- **OS:** Ubuntu 24.04.4 LTS (x86_64), kernel 6.18.44
- **Python:** 3.11.15
- **Node.js:** v22.22.2 (npm 10.9.7; node20/node21/node22 and nvm under `/opt`)
- **Git:** 2.43.0
- **Ruby:** 3.1.6 / 3.2.6 / 3.3.6 (rbenv)
- **Java build tools:** Apache Maven 3.9.11, Gradle 8.14.3
- **Browser:** Chromium pre-installed for Playwright (`/opt/pw-browsers`)
- **Other:** rclone, Claude Code CLI (`/opt/claude-code`), env-runner

## Session characteristics

- Ephemeral, isolated container; repository cloned fresh at session start;
  reclaimed after inactivity. Anything durable must be committed and pushed.
- Outbound HTTPS via a pre-configured agent proxy with its own CA bundle.
- Fixed per-session writable-disk allowance.
- Skill sync: the account's enabled skills materialise under
  `/root/.claude/skills/synced/<bucket>/` at session start — the source this
  backup's `skills/` folder was copied from (see `verify_sync.py`).
