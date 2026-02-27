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

Pass flags or env vars:
- `--url` or `KUMA_URL`
- token-only auth: `--token` or `KUMA_TOKEN` (login session token for `loginByToken`)
- user/pass auth: `--username` + `--password` or `KUMA_USERNAME` + `KUMA_PASSWORD`
- 2FA auth: pass `--token` together with `--username` and `--password` (TOTP code)

## Usage

List monitors:

```bash
uv run kumacli --url http://localhost:3001 --token "$KUMA_TOKEN" monitors list
```

Create maintenance for monitors:

```bash
uv run kumacli --url http://localhost:3001 --token "$KUMA_TOKEN" maintenance create \
  --title "Deploy window" \
  --strategy single \
  --date-start "2026-03-01 22:00" \
  --date-end "2026-03-01 23:00" \
  --monitor-id 1 --monitor-id 2
```

Update maintenance:

```bash
uv run kumacli --url http://localhost:3001 --token "$KUMA_TOKEN" maintenance update \
  --id 5 \
  --title "Updated title" \
  --monitor-id 2,3
```

Delete maintenance:

```bash
uv run kumacli --url http://localhost:3001 --token "$KUMA_TOKEN" maintenance delete --id 5
```
