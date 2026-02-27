# kumacli

CLI for Uptime Kuma.

Features:
- list monitors with current status
- create maintenance for selected monitors
- update maintenance fields and linked monitors
- delete maintenance

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
