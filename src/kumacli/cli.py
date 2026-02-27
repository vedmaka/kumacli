"""CLI for Uptime Kuma monitor status and maintenance operations."""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Silence known upstream warning in uptime-kuma-api docstring parsing.
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"uptime_kuma_api\.api")
warnings.filterwarnings("ignore", category=SyntaxWarning, message=r".*invalid escape sequence.*")
from uptime_kuma_api import MaintenanceStrategy, UptimeKumaApi


class CliError(Exception):
    """Expected user-facing CLI error."""


@dataclass
class ConnectionConfig:
    url: str
    username: str | None
    password: str | None
    timeout: float
    insecure: bool


def _load_dotenv(path: str | Path = ".env") -> dict[str, str]:
    """Load simple KEY=VALUE pairs from .env file."""
    dotenv_path = Path(path)
    if not dotenv_path.is_file():
        return {}

    loaded: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        loaded[key] = value
    return loaded


def _env_value(dotenv: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        runtime_value = os.getenv(key)
        if runtime_value:
            return runtime_value
        dotenv_value = dotenv.get(key)
        if dotenv_value:
            return dotenv_value
    return None


def _parse_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    dotenv = _load_dotenv()
    parser = argparse.ArgumentParser(
        prog="kumacli",
        description="CLI interface for Uptime Kuma",
    )
    parser.add_argument(
        "--url",
        "--host",
        dest="url",
        default=_env_value(dotenv, "KUMACLI_HOST", "KUMA_URL"),
        help="Uptime Kuma base URL",
    )
    parser.add_argument(
        "--username",
        default=_env_value(dotenv, "KUMACLI_USERNAME", "KUMA_USERNAME"),
        help="Uptime Kuma username",
    )
    parser.add_argument(
        "--password",
        default=_env_value(dotenv, "KUMACLI_PASSWORD", "KUMA_PASSWORD"),
        help="Uptime Kuma password",
    )
    parser.add_argument("--timeout", default=None, type=float, help="API timeout in seconds")
    parser.add_argument(
        "--insecure",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Disable TLS certificate verification",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    monitors_parser = subparsers.add_parser("monitors", help="Monitor operations")
    monitors_sub = monitors_parser.add_subparsers(dest="monitors_command", required=True)
    monitors_list = monitors_sub.add_parser("list", help="List monitors and statuses")
    monitors_list.add_argument("--json", action="store_true", help="Output JSON")

    maintenance_parser = subparsers.add_parser("maintenance", help="Maintenance operations")
    maintenance_sub = maintenance_parser.add_subparsers(dest="maintenance_command", required=True)

    create_parser = maintenance_sub.add_parser("create", help="Create maintenance and attach monitors")
    create_parser.add_argument("--title", required=True, help="Maintenance title")
    create_parser.add_argument(
        "--strategy",
        default=MaintenanceStrategy.MANUAL.value,
        help="Strategy: manual|single|recurring-interval|recurring-weekday|recurring-day-of-month|cron",
    )
    _add_maintenance_payload_args(create_parser, include_title=False)
    _add_monitor_id_arg(create_parser, required=True)
    create_parser.add_argument("--json", action="store_true", help="Output JSON")

    update_parser = maintenance_sub.add_parser("update", help="Update maintenance fields and/or monitor links")
    update_parser.add_argument("--id", required=True, type=int, help="Maintenance ID")
    update_parser.add_argument("--title", help="Maintenance title")
    update_parser.add_argument(
        "--strategy",
        help="Strategy: manual|single|recurring-interval|recurring-weekday|recurring-day-of-month|cron",
    )
    _add_maintenance_payload_args(update_parser, include_title=False)
    _add_monitor_id_arg(update_parser, required=False)
    update_parser.add_argument("--json", action="store_true", help="Output JSON")

    delete_parser = maintenance_sub.add_parser("delete", help="Delete maintenance")
    delete_parser.add_argument("--id", required=True, type=int, help="Maintenance ID")
    delete_parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args(argv)

    if args.timeout is None:
        timeout_env = _env_value(dotenv, "KUMACLI_TIMEOUT", "KUMA_TIMEOUT")
        if timeout_env is not None:
            try:
                args.timeout = float(timeout_env)
            except ValueError:
                parser.error(f"Invalid timeout value '{timeout_env}' in KUMACLI_TIMEOUT/KUMA_TIMEOUT")
        else:
            args.timeout = 10.0

    if args.insecure is None:
        insecure_env = _env_value(dotenv, "KUMACLI_INSECURE", "KUMA_INSECURE")
        if insecure_env is not None:
            parsed = _parse_bool(insecure_env)
            if parsed is None:
                parser.error(
                    f"Invalid insecure value '{insecure_env}' in KUMACLI_INSECURE/KUMA_INSECURE "
                    "(use true/false)"
                )
            args.insecure = parsed
        else:
            args.insecure = False

    return args


def _add_maintenance_payload_args(parser: argparse.ArgumentParser, *, include_title: bool) -> None:
    if include_title:
        parser.add_argument("--title", required=True, help="Maintenance title")
    parser.add_argument("--description", help="Maintenance description")
    activity = parser.add_mutually_exclusive_group()
    activity.add_argument("--active", dest="active", action="store_true", help="Set active")
    activity.add_argument("--inactive", dest="active", action="store_false", help="Set inactive")
    parser.set_defaults(active=None)
    parser.add_argument("--interval-day", type=int, help="Interval day for recurring strategy")
    parser.add_argument("--date-start", help="Date-time: YYYY-MM-DD HH:MM[:SS] or YYYY-MM-DD")
    parser.add_argument("--date-end", help="Date-time: YYYY-MM-DD HH:MM[:SS] or YYYY-MM-DD")
    parser.add_argument("--time-start", help="HH:MM")
    parser.add_argument("--time-end", help="HH:MM")
    parser.add_argument("--weekday", action="append", type=int, default=[], help="Weekday 0-6. Repeatable")
    parser.add_argument(
        "--day-of-month",
        action="append",
        default=[],
        help='Day of month (1-31 or "lastDay1"). Repeatable',
    )
    parser.add_argument("--cron", help="Cron expression")
    parser.add_argument("--duration-minutes", type=int, help="Duration for cron strategy")
    parser.add_argument("--timezone", help="Timezone, e.g. Europe/Berlin")


def _add_monitor_id_arg(parser: argparse.ArgumentParser, *, required: bool) -> None:
    parser.add_argument(
        "--monitor-id",
        action="append",
        default=[],
        required=required,
        help="Monitor ID. Repeatable, comma-separated accepted",
    )


def _parse_strategy(value: str) -> MaintenanceStrategy:
    normalized = value.strip().lower()
    for candidate in MaintenanceStrategy:
        if candidate.value == normalized:
            return candidate
    names = ", ".join(s.value for s in MaintenanceStrategy)
    raise CliError(f"Invalid strategy '{value}'. Allowed: {names}")


def _normalize_datetime(value: str) -> str:
    raw = value.strip().replace("T", " ")
    patterns = ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")
    for pattern in patterns:
        try:
            parsed = datetime.strptime(raw, pattern)
            if pattern == "%Y-%m-%d":
                return parsed.strftime("%Y-%m-%d 00:00:00")
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise CliError(f"Invalid datetime '{value}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM[:SS]")


def _parse_hhmm(value: str) -> dict[str, int]:
    try:
        hours_str, minutes_str = value.split(":", 1)
        hours = int(hours_str)
        minutes = int(minutes_str)
    except ValueError as exc:
        raise CliError(f"Invalid time '{value}'. Use HH:MM") from exc
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise CliError(f"Invalid time '{value}'. Use HH:MM")
    return {"hours": hours, "minutes": minutes}


def _parse_day_of_month(values: list[str]) -> list[int | str]:
    parsed: list[int | str] = []
    for value in values:
        for token in value.split(","):
            item = token.strip()
            if not item:
                continue
            if item.lower().startswith("lastday"):
                parsed.append(item)
                continue
            try:
                day = int(item)
            except ValueError as exc:
                raise CliError(f"Invalid day-of-month '{item}'") from exc
            if not (1 <= day <= 31):
                raise CliError(f"day-of-month out of range: {day}")
            parsed.append(day)
    return parsed


def _parse_monitor_ids(values: list[str]) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for value in values:
        for token in value.split(","):
            item = token.strip()
            if not item:
                continue
            try:
                monitor_id = int(item)
            except ValueError as exc:
                raise CliError(f"Invalid monitor id '{item}'") from exc
            if monitor_id in seen:
                continue
            seen.add(monitor_id)
            ids.append(monitor_id)
    return ids


def _build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if getattr(args, "title", None) is not None:
        payload["title"] = args.title
    if getattr(args, "strategy", None):
        payload["strategy"] = _parse_strategy(args.strategy)
    if args.description is not None:
        payload["description"] = args.description
    if args.active is not None:
        payload["active"] = args.active
    if args.interval_day is not None:
        payload["intervalDay"] = args.interval_day

    if args.date_start:
        payload["dateRange"] = [_normalize_datetime(args.date_start)]
        if args.date_end:
            payload["dateRange"].append(_normalize_datetime(args.date_end))
    elif args.date_end:
        raise CliError("--date-end requires --date-start")

    if args.time_start or args.time_end:
        if not (args.time_start and args.time_end):
            raise CliError("--time-start and --time-end must be used together")
        payload["timeRange"] = [_parse_hhmm(args.time_start), _parse_hhmm(args.time_end)]

    if args.weekday:
        for day in args.weekday:
            if not (0 <= day <= 6):
                raise CliError(f"weekday out of range: {day}")
        payload["weekdays"] = args.weekday

    if args.day_of_month:
        payload["daysOfMonth"] = _parse_day_of_month(args.day_of_month)

    if args.cron is not None:
        payload["cron"] = args.cron
    if args.duration_minutes is not None:
        payload["durationMinutes"] = args.duration_minutes
    if args.timezone is not None:
        payload["timezoneOption"] = args.timezone
    return payload


def _to_connection_config(args: argparse.Namespace) -> ConnectionConfig:
    if not args.url:
        raise CliError("Missing --url/--host or KUMACLI_HOST/KUMA_URL")
    if not args.username or not args.password:
        raise CliError(
            "Missing --username/--password or "
            "KUMACLI_USERNAME/KUMA_USERNAME + KUMACLI_PASSWORD/KUMA_PASSWORD"
        )
    return ConnectionConfig(
        url=args.url,
        username=args.username,
        password=args.password,
        timeout=args.timeout,
        insecure=args.insecure,
    )


def _connect(args: argparse.Namespace) -> UptimeKumaApi:
    cfg = _to_connection_config(args)
    api = UptimeKumaApi(cfg.url, timeout=cfg.timeout, ssl_verify=not cfg.insecure)
    try:
        api.login(username=cfg.username, password=cfg.password)
    except Exception as exc:
        raise CliError("Username/password auth failed") from exc
    return api


def _print_monitors(monitors: list[dict[str, Any]], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(monitors, indent=2))
        return
    print("id\tname\tstatus\tactive\ttype")
    for item in monitors:
        print(f"{item['id']}\t{item['name']}\t{item['status']}\t{item['active']}\t{item['type']}")


def _validate_monitor_ids(api: UptimeKumaApi, monitor_ids: list[int]) -> None:
    available = {int(m["id"]) for m in api.get_monitors()}
    missing = [str(mid) for mid in monitor_ids if mid not in available]
    if missing:
        raise CliError(f"Unknown monitor IDs: {', '.join(missing)}")


def _run_monitors_list(api: UptimeKumaApi, args: argparse.Namespace) -> None:
    rows = []
    for monitor in sorted(api.get_monitors(), key=lambda x: int(x.get("id", 0))):
        mid = int(monitor["id"])
        status = api.get_monitor_status(mid)
        rows.append(
            {
                "id": mid,
                "name": monitor.get("name", ""),
                "status": status.name.lower(),
                "active": bool(monitor.get("active")),
                "type": str(monitor.get("type", "")),
            }
        )
    _print_monitors(rows, as_json=args.json)


def _run_maintenance_create(api: UptimeKumaApi, args: argparse.Namespace) -> None:
    payload = _build_payload(args)
    monitor_ids = _parse_monitor_ids(args.monitor_id)
    if not monitor_ids:
        raise CliError("At least one --monitor-id is required")
    _validate_monitor_ids(api, monitor_ids)
    result = api.add_maintenance(**payload)
    maintenance_id = result.get("maintenanceID") or result.get("maintenanceId")
    if not isinstance(maintenance_id, int):
        raise CliError("Uptime Kuma response missing maintenance ID")
    api.add_monitor_maintenance(maintenance_id, [{"id": monitor_id} for monitor_id in monitor_ids])
    output = {"maintenance_id": maintenance_id, "message": result.get("msg", "ok"), "monitor_ids": monitor_ids}
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(
            f"Created maintenance {output['maintenance_id']} "
            f"for monitors {','.join(str(i) for i in output['monitor_ids'])}"
        )


def _run_maintenance_update(api: UptimeKumaApi, args: argparse.Namespace) -> None:
    payload = _build_payload(args)
    monitor_ids = _parse_monitor_ids(args.monitor_id)
    if not payload and not monitor_ids:
        raise CliError("Nothing to update")

    if payload:
        api.edit_maintenance(args.id, **payload)

    if monitor_ids:
        _validate_monitor_ids(api, monitor_ids)
        api.add_monitor_maintenance(args.id, [{"id": monitor_id} for monitor_id in monitor_ids])

    output = {"maintenance_id": args.id, "updated_fields": sorted(payload.keys()), "monitor_ids": monitor_ids}
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Updated maintenance {args.id}")


def _run_maintenance_delete(api: UptimeKumaApi, args: argparse.Namespace) -> None:
    result = api.delete_maintenance(args.id)
    output = {"maintenance_id": args.id, "message": result.get("msg", "deleted")}
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"Deleted maintenance {args.id}")


def _run(api: UptimeKumaApi, args: argparse.Namespace) -> None:
    if args.command == "monitors" and args.monitors_command == "list":
        _run_monitors_list(api, args)
        return
    if args.command == "maintenance" and args.maintenance_command == "create":
        _run_maintenance_create(api, args)
        return
    if args.command == "maintenance" and args.maintenance_command == "update":
        _run_maintenance_update(api, args)
        return
    if args.command == "maintenance" and args.maintenance_command == "delete":
        _run_maintenance_delete(api, args)
        return
    raise CliError("Unknown command")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    api = None
    try:
        api = _connect(args)
        _run(api, args)
        return 0
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if api is not None:
            api.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
