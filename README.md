# kumacli

CLI for Uptime Kuma.

Features:
- list monitors with current status
- get monitor details
- add/update/delete monitors
- pause/resume monitors
- create maintenance for selected monitors
- update maintenance fields and linked monitors
- delete maintenance
- list/get/pause/resume maintenance

## Install

```bash
uv sync --all-groups
```

## Auth

Pass flags or env vars (`.env` in current dir auto-loaded):
- `--url`/`--host` or `KUMACLI_HOST` (`KUMA_URL` still supported)
- username/password auth: `--username` + `--password` or `KUMACLI_USERNAME` + `KUMACLI_PASSWORD` (`KUMA_*` supported)
- timeout: `--timeout` or `KUMACLI_TIMEOUT`/`KUMA_TIMEOUT`
- TLS verify toggle: `--insecure`/`--no-insecure` or `KUMACLI_INSECURE`/`KUMA_INSECURE` (`true|false|1|0|yes|no|on|off`)
- CLI params always override env values

## Usage

List monitors:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors list
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
  --field "interval=60"
```

Update monitor:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors update \
  --id 1 \
  --name "Main API v2" \
  --field "maxretries=5"
```

Delete/pause/resume monitor:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors pause --id 1
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors resume --id 1
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" monitors delete --id 1
```

Create maintenance for monitors:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance create \
  --title "Deploy window" \
  --strategy single \
  --date-start "2026-03-01 22:00" \
  --date-end "2026-03-01 23:00" \
  --monitor-id 1 --monitor-id 2
```

Update maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance update \
  --id 5 \
  --title "Updated title" \
  --monitor-id 2,3
```

Delete maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance delete --id 5
```

List/get/pause/resume maintenance:

```bash
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance list --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance get --id 5 --json
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance pause --id 5
uv run kumacli --url http://localhost:3001 --username "$KUMA_USERNAME" --password "$KUMA_PASSWORD" maintenance resume --id 5
```
