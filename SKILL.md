# kumacli skill

Use this when agent must operate Uptime Kuma from terminal.

## Scope

- monitor operations: list/get/add/update/delete/pause/resume
- maintenance operations: list/get/create/update/delete/pause/resume
- machine-friendly output via `--json`

## Preflight

```bash
uv sync --all-groups
uv run kumacli --help
uv run kumacli monitors --help
uv run kumacli maintenance --help
```

## Auth

Set host via `--url`/`--host` or env `KUMACLI_HOST` (`KUMA_URL` fallback).

`.env` in current dir auto-loaded. Params override env.

Auth mode:
- username/password only: `--username` + `--password`

Other connection params:
- timeout: `--timeout` or `KUMACLI_TIMEOUT`/`KUMA_TIMEOUT`
- TLS verify: `--insecure` / `--no-insecure` or `KUMACLI_INSECURE`/`KUMA_INSECURE`

Important:
- session token/API key auth not supported

## Command map

- `monitors list [--json]`
- `monitors get --id <id> [--json]`
- `monitors add --name <name> --type <type> [payload args] [--json]`
- `monitors update --id <id> [payload args] [--json]`
- `monitors delete --id <id> [--json]`
- `monitors pause --id <id> [--json]`
- `monitors resume --id <id> [--json]`
- `maintenance list [--json]`
- `maintenance get --id <id> [--json]`
- `maintenance create --title <title> --monitor-id <id[,id]> [maintenance args] [--json]`
- `maintenance update --id <id> [maintenance args] [--monitor-id ...] [--json]`
- `maintenance delete --id <id> [--json]`
- `maintenance pause --id <id> [--json]`
- `maintenance resume --id <id> [--json]`

## Workflow

1. list monitors, pick IDs
2. add/update/pause/resume monitors as needed
3. create/update/pause/resume maintenance windows
4. prefer `--json` for automation/parsing

List monitors:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors list --json
```

Get monitor:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors get --id 1 --json
```

Add monitor:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors add \
  --name "Main API" \
  --type http \
  --field "url=https://example.com/health" \
  --field "interval=60" \
  --json
```

Update monitor:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors update \
  --id 1 \
  --field "maxretries=5" \
  --json
```

Pause/resume/delete monitor:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors pause --id 1 --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors resume --id 1 --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors delete --id 1 --json
```

Create maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance create \
  --title "Deploy window" \
  --strategy single \
  --date-start "2026-03-01 22:00" \
  --date-end "2026-03-01 23:00" \
  --monitor-id 1,2 \
  --json
```

Update maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance update \
  --id 5 \
  --title "Deploy window updated" \
  --monitor-id 3 \
  --json
```

Delete maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance delete \
  --id 5 \
  --json
```

List/get/pause/resume maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance list --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance get --id 5 --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance pause --id 5 --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance resume --id 5 --json
```

## Payload args

Monitor add/update payload:
- `--name`, `--type`
- `--field key=value` (repeatable; JSON scalars parse automatically: `60`, `true`)
- `--data-json '{"key":"value"}'`
- `--data-file payload.json`
- merge order: `--data-file` -> `--data-json` -> `--field` -> explicit `--name/--type`

Maintenance payload:
- strategy: `manual|single|recurring-interval|recurring-weekday|recurring-day-of-month|cron`
- date/time: `--date-start`, `--date-end`, `--time-start`, `--time-end`
- recurrence: `--interval-day`, `--weekday`, `--day-of-month`, `--cron`, `--duration-minutes`, `--timezone`
- state: `--active` / `--inactive`

## Guardrails

- monitor IDs validated; unknown IDs fail fast
- `--date-end` requires `--date-start`
- `--time-start` and `--time-end` must be passed together
- update requires at least one field or `--monitor-id`
- monitor add requires `name` + `type`
- monitor update requires at least one payload field

## Troubleshooting

- `Timed out while waiting for event Event.AUTO_LOGIN`: auth missing/invalid
- `error: Missing --username/--password`: pass flags or set env vars
- `error: Unknown monitor IDs: ...`: run `monitors list`, retry with valid IDs
