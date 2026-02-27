# kumacli skill

Use this when agent must operate Uptime Kuma from terminal.

## Scope

- list monitors + statuses
- create maintenance for selected monitors
- update maintenance fields and monitor links
- delete maintenance

## Preflight

```bash
uv sync --all-groups
uv run kumacli --help
```

## Auth

Set `--url` or `KUMA_URL`.

Auth modes:
- username/password: `--username` + `--password`
- username/password + 2FA: add `--token <TOTP>`
- token-only: `--token <login session token>` (uses Kuma `loginByToken`)

Important:
- token-only expects Kuma login session token
- token-only is not an API key mode

## Core workflow

1. list monitors, choose IDs
2. create/update/delete maintenance
3. prefer `--json` for machine parsing

List monitors:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors list --json
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

## Guardrails

- monitor IDs validated; unknown IDs fail fast
- `--date-end` requires `--date-start`
- `--time-start` and `--time-end` must be passed together
- update requires at least one field or `--monitor-id`

## Troubleshooting

- `Timed out while waiting for event Event.AUTO_LOGIN`: auth missing/invalid
- if token-only fails, switch to username/password or refresh Kuma session token
