# kumacli

CLI for Uptime Kuma automation from terminal.

## Highlights

- monitor commands: `list`, `get`, `add`, `update`, `delete`, `pause`, `resume`
- maintenance commands: `list`, `get`, `create`, `update`, `delete`, `pause`, `resume`
- JSON output mode for scripts: `--json`
- `.env` auto-load with CLI-overrides-env behavior

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Command Reference](#command-reference)
- [Examples](#examples)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Requirements

- Python `>=3.13`
- `uv`
- reachable Uptime Kuma instance
- Uptime Kuma username/password

## Installation

```bash
uv sync --all-groups
```

## Quick Start

```bash
export KUMACLI_HOST="http://localhost:3001"
export KUMACLI_USERNAME="admin"
export KUMACLI_PASSWORD="secret"

uv run kumacli monitors list --json
```

## Configuration

`.env` in current dir is auto-loaded.

| Flag | Env | Required | Notes |
|---|---|---|---|
| `--url` / `--host` | `KUMACLI_HOST` (`KUMA_URL` fallback) | yes | Uptime Kuma base URL |
| `--username` | `KUMACLI_USERNAME` (`KUMA_USERNAME`) | yes | username/password auth only |
| `--password` | `KUMACLI_PASSWORD` (`KUMA_PASSWORD`) | yes | username/password auth only |
| `--timeout` | `KUMACLI_TIMEOUT` (`KUMA_TIMEOUT`) | no | default `10` seconds |
| `--insecure` / `--no-insecure` | `KUMACLI_INSECURE` (`KUMA_INSECURE`) | no | bool: `true/false/1/0/yes/no/on/off` |

Rules:
- CLI flags override env values
- API key/session token auth not supported

## Command Reference

Global help:

```bash
uv run kumacli --help
uv run kumacli monitors --help
uv run kumacli maintenance --help
```

Monitor commands:

```text
kumacli monitors list [--json]
kumacli monitors get --id <id> [--json]
kumacli monitors add --name <name> --type <type> [--field key=value ...] [--data-json '{...}'] [--data-file payload.json] [--json]
kumacli monitors update --id <id> [--name <name>] [--type <type>] [--field key=value ...] [--data-json '{...}'] [--data-file payload.json] [--json]
kumacli monitors delete --id <id> [--json]
kumacli monitors pause --id <id> [--json]
kumacli monitors resume --id <id> [--json]
```

Maintenance commands:

```text
kumacli maintenance list [--json]
kumacli maintenance get --id <id> [--json]
kumacli maintenance create --title <title> --monitor-id <id[,id]> [options] [--json]
kumacli maintenance update --id <id> [options] [--monitor-id <id[,id]> ...] [--json]
kumacli maintenance delete --id <id> [--json]
kumacli maintenance pause --id <id> [--json]
kumacli maintenance resume --id <id> [--json]
```

Monitor payload options (`add`/`update`):
- `--field key=value` repeatable
- `--data-json '{"k":"v"}'`
- `--data-file payload.json`
- merge order: `--data-file` -> `--data-json` -> `--field` -> explicit `--name/--type`

Maintenance options:
- strategy: `manual|single|recurring-interval|recurring-weekday|recurring-day-of-month|cron`
- date range: `--date-start`, `--date-end`
- time range: `--time-start`, `--time-end`
- recurrence: `--interval-day`, `--weekday`, `--day-of-month`, `--cron`, `--duration-minutes`, `--timezone`
- state: `--active` / `--inactive`

## Examples

Add monitor:

```bash
uv run kumacli monitors add \
  --name "Main API" \
  --type http \
  --field "url=https://example.com/health" \
  --field "interval=60"
```

Update monitor:

```bash
uv run kumacli monitors update --id 1 --field "maxretries=5"
```

Create maintenance:

```bash
uv run kumacli maintenance create \
  --title "Deploy window" \
  --strategy single \
  --date-start "2026-03-01 22:00" \
  --date-end "2026-03-01 23:00" \
  --monitor-id 1 --monitor-id 2
```

## Development

```bash
uv sync --all-groups
uv run pytest -q
```

## Troubleshooting

- `error: Missing --url/--host...`: set URL via flag or env
- `error: Missing --username/--password...`: pass creds via flags/env
- `error: Unknown monitor IDs: ...`: run `monitors list`, retry with valid IDs
- `Timed out while waiting for event Event.AUTO_LOGIN`: invalid auth or unreachable Kuma
