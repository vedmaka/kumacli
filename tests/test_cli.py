from __future__ import annotations

from uptime_kuma_api import MaintenanceStrategy, MonitorStatus

from kumacli import cli


class FakeApi:
    instances: list["FakeApi"] = []

    def __init__(self, url: str, timeout: float = 10, ssl_verify: bool = True):
        self.url = url
        self.timeout = timeout
        self.ssl_verify = ssl_verify
        self.login_calls = []
        self.disconnected = False
        self.created_payload = None
        self.updated_payload = None
        self.updated_id = None
        self.deleted_id = None
        self.monitor_links = []
        FakeApi.instances.append(self)

    def login(self, username=None, password=None):
        self.login_calls.append({"username": username, "password": password})
        return {}

    def disconnect(self):
        self.disconnected = True

    def get_monitors(self):
        return [
            {"id": 1, "name": "api", "active": 1, "type": "http"},
            {"id": 2, "name": "db", "active": 0, "type": "port"},
        ]

    def get_monitor_status(self, monitor_id: int):
        if monitor_id == 1:
            return MonitorStatus.UP
        return MonitorStatus.DOWN

    def add_maintenance(self, **kwargs):
        self.created_payload = kwargs
        return {"maintenanceID": 42, "msg": "Added Successfully."}

    def edit_maintenance(self, id_: int, **kwargs):
        self.updated_id = id_
        self.updated_payload = kwargs
        return {"maintenanceID": id_, "msg": "Saved."}

    def delete_maintenance(self, id_: int):
        self.deleted_id = id_
        return {"msg": "Deleted Successfully."}

    def add_monitor_maintenance(self, id_: int, monitors: list[dict]):
        self.monitor_links.append({"maintenance_id": id_, "monitors": monitors})
        return {"msg": "Added Successfully."}


def _run(monkeypatch, args: list[str]):
    FakeApi.instances.clear()
    monkeypatch.setattr(cli, "UptimeKumaApi", FakeApi)
    return cli.main(args)


def _clear_env(monkeypatch):
    for key in (
        "KUMACLI_HOST",
        "KUMACLI_USERNAME",
        "KUMACLI_PASSWORD",
        "KUMACLI_TIMEOUT",
        "KUMACLI_INSECURE",
        "KUMA_URL",
        "KUMA_USERNAME",
        "KUMA_PASSWORD",
        "KUMA_TIMEOUT",
        "KUMA_INSECURE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_dotenv_connection_defaults(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "KUMACLI_HOST=http://dotenv-host\nKUMACLI_USERNAME=dotenv-user\nKUMACLI_PASSWORD=dotenv-pass\n",
        encoding="utf-8",
    )

    code = _run(monkeypatch, ["monitors", "list", "--json"])
    assert code == 0
    api = FakeApi.instances[0]
    assert api.url == "http://dotenv-host"
    assert api.login_calls[0] == {"username": "dotenv-user", "password": "dotenv-pass"}


def test_cli_params_override_dotenv(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "KUMACLI_HOST=http://dotenv-host\nKUMACLI_USERNAME=dotenv-user\nKUMACLI_PASSWORD=dotenv-pass\n",
        encoding="utf-8",
    )

    code = _run(
        monkeypatch,
        [
            "--host",
            "http://flag-host",
            "--username",
            "flag-user",
            "--password",
            "flag-pass",
            "monitors",
            "list",
            "--json",
        ],
    )
    assert code == 0
    api = FakeApi.instances[0]
    assert api.url == "http://flag-host"
    assert api.login_calls[0] == {"username": "flag-user", "password": "flag-pass"}


def test_dotenv_timeout_insecure(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "KUMACLI_HOST=http://dotenv-host\nKUMACLI_USERNAME=dotenv-user\nKUMACLI_PASSWORD=dotenv-pass\n"
        "KUMACLI_TIMEOUT=33\nKUMACLI_INSECURE=true\n",
        encoding="utf-8",
    )

    code = _run(monkeypatch, ["monitors", "list", "--json"])
    assert code == 0
    api = FakeApi.instances[0]
    assert api.url == "http://dotenv-host"
    assert api.timeout == 33.0
    assert api.ssl_verify is False
    assert api.login_calls[0] == {"username": "dotenv-user", "password": "dotenv-pass"}


def test_cli_overrides_dotenv_timeout_insecure(monkeypatch, tmp_path):
    _clear_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "KUMACLI_HOST=http://dotenv-host\nKUMACLI_USERNAME=dotenv-user\nKUMACLI_PASSWORD=dotenv-pass\n"
        "KUMACLI_TIMEOUT=44\nKUMACLI_INSECURE=true\n",
        encoding="utf-8",
    )

    code = _run(
        monkeypatch,
        [
            "--host",
            "http://flag-host",
            "--username",
            "flag-user",
            "--password",
            "flag-pass",
            "--timeout",
            "7",
            "--no-insecure",
            "monitors",
            "list",
            "--json",
        ],
    )
    assert code == 0
    api = FakeApi.instances[0]
    assert api.url == "http://flag-host"
    assert api.timeout == 7.0
    assert api.ssl_verify is True
    assert api.login_calls[0] == {"username": "flag-user", "password": "flag-pass"}


def test_monitors_list_json(monkeypatch, capsys):
    code = _run(
        monkeypatch,
        ["--url", "http://kuma", "--username", "admin", "--password", "secret", "monitors", "list", "--json"],
    )
    out = capsys.readouterr().out
    assert code == 0
    assert '"name": "api"' in out
    assert '"status": "up"' in out
    assert FakeApi.instances[0].disconnected is True


def test_maintenance_create(monkeypatch):
    code = _run(
        monkeypatch,
        [
            "--url",
            "http://kuma",
            "--username",
            "admin",
            "--password",
            "secret",
            "maintenance",
            "create",
            "--title",
            "deploy",
            "--monitor-id",
            "1,2",
        ],
    )
    assert code == 0
    api = FakeApi.instances[0]
    assert api.created_payload["title"] == "deploy"
    assert api.created_payload["strategy"] == MaintenanceStrategy.MANUAL
    assert api.monitor_links == [{"maintenance_id": 42, "monitors": [{"id": 1}, {"id": 2}]}]


def test_maintenance_update_with_monitors(monkeypatch):
    code = _run(
        monkeypatch,
        [
            "--url",
            "http://kuma",
            "--username",
            "admin",
            "--password",
            "secret",
            "maintenance",
            "update",
            "--id",
            "9",
            "--title",
            "new-title",
            "--monitor-id",
            "2",
        ],
    )
    assert code == 0
    api = FakeApi.instances[0]
    assert api.updated_id == 9
    assert api.updated_payload["title"] == "new-title"
    assert api.monitor_links == [{"maintenance_id": 9, "monitors": [{"id": 2}]}]


def test_maintenance_delete(monkeypatch):
    code = _run(
        monkeypatch,
        ["--url", "http://kuma", "--username", "admin", "--password", "secret", "maintenance", "delete", "--id", "5"],
    )
    assert code == 0
    assert FakeApi.instances[0].deleted_id == 5


def test_login_with_username_password(monkeypatch):
    code = _run(
        monkeypatch,
        [
            "--url",
            "http://kuma",
            "--username",
            "admin",
            "--password",
            "secret",
            "monitors",
            "list",
            "--json",
        ],
    )
    assert code == 0
    assert FakeApi.instances[0].login_calls[0] == {"username": "admin", "password": "secret"}


def test_errors_without_username_password(monkeypatch, capsys):
    code = _run(monkeypatch, ["--url", "http://kuma", "monitors", "list", "--json"])
    err = capsys.readouterr().err
    assert code == 2
    assert "Missing --username/--password" in err


def test_errors_on_unknown_monitor(monkeypatch, capsys):
    code = _run(
        monkeypatch,
        [
            "--url",
            "http://kuma",
            "--username",
            "admin",
            "--password",
            "secret",
            "maintenance",
            "create",
            "--title",
            "deploy",
            "--monitor-id",
            "999",
        ],
    )
    err = capsys.readouterr().err
    assert code == 2
    assert "Unknown monitor IDs: 999" in err
