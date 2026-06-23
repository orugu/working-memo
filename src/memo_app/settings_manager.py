import json
from pathlib import Path
from platformdirs import user_data_dir


_DEFAULTS = {
    # ── DB 서버 (PostgreSQL 접속) ─────────────────────────────────────────
    "db_host":          "devlovers.cloud",  # 외부 호스트 (fallback)
    "db_host_internal": "",                 # 내부 IP (우선 시도, 빈 값이면 스킵)
    "db_port":          "40916",
    "db_name":          "working_memo",
    "db_username": "",   # PostgreSQL 서버 계정
    "db_password": "",   # PostgreSQL 서버 비밀번호
    # ── 앱 사용자 (Working Memo 계정) ─────────────────────────────────────
    "app_username": "",
    "app_password": "",
    # ── UI ───────────────────────────────────────────────────────────────
    "corner_size":      20,
    "overlay_width":    380,
    "leave_delay":      400,
    "animation":        True,
    "anim_duration":    220,
    # ── 디스플레이별 코너 설정 [{corner_size, enabled}, ...] ─────────────
    "display_configs":  [],
}


class SettingsManager:
    def __init__(self):
        data_dir = Path(user_data_dir("WorkingMemo", "WorkingMemo"))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "settings.json"
        self._data: dict = dict(_DEFAULTS)
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                stored = json.loads(self.path.read_text(encoding="utf-8"))
                # 이전 버전 마이그레이션: display_name/email → app_username/app_password
                if "display_name" in stored and not stored.get("app_username"):
                    stored["app_username"] = stored.pop("display_name", "")
                if "email" in stored and not stored.get("app_password"):
                    stored["app_password"] = stored.pop("email", "")
                self._data.update({k: stored[k] for k in _DEFAULTS if k in stored})
            except Exception:
                pass

    def _save(self):
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── DB 서버 ───────────────────────────────────────────────────────────

    @property
    def db_host(self) -> str:
        return self._data["db_host"]

    @db_host.setter
    def db_host(self, v: str):
        self._data["db_host"] = v; self._save()

    @property
    def db_host_internal(self) -> str:
        return self._data.get("db_host_internal", "")

    @db_host_internal.setter
    def db_host_internal(self, v: str):
        self._data["db_host_internal"] = v; self._save()

    @property
    def db_port(self) -> str:
        return self._data["db_port"]

    @db_port.setter
    def db_port(self, v: str):
        self._data["db_port"] = v; self._save()

    @property
    def db_name(self) -> str:
        return self._data["db_name"]

    @db_name.setter
    def db_name(self, v: str):
        self._data["db_name"] = v; self._save()

    @property
    def db_username(self) -> str:
        return self._data["db_username"]

    @db_username.setter
    def db_username(self, v: str):
        self._data["db_username"] = v; self._save()

    @property
    def db_password(self) -> str:
        return self._data["db_password"]

    @db_password.setter
    def db_password(self, v: str):
        self._data["db_password"] = v; self._save()

    # ── 앱 사용자 ─────────────────────────────────────────────────────────

    @property
    def app_username(self) -> str:
        return self._data["app_username"]

    @app_username.setter
    def app_username(self, v: str):
        self._data["app_username"] = v; self._save()

    @property
    def app_password(self) -> str:
        return self._data["app_password"]

    @app_password.setter
    def app_password(self, v: str):
        self._data["app_password"] = v; self._save()

    # ── UI ────────────────────────────────────────────────────────────────

    @property
    def corner_size(self) -> int:
        return self._data["corner_size"]

    @corner_size.setter
    def corner_size(self, v: int):
        self._data["corner_size"] = max(5, min(100, v)); self._save()

    @property
    def display_configs(self) -> list[dict]:
        return self._data.get("display_configs", [])

    @display_configs.setter
    def display_configs(self, v: list[dict]):
        self._data["display_configs"] = v
        self._save()

    @property
    def animation(self) -> bool:
        return bool(self._data.get("animation", True))

    @animation.setter
    def animation(self, v: bool):
        self._data["animation"] = v; self._save()

    @property
    def anim_duration(self) -> int:
        return int(self._data.get("anim_duration", 220))

    @anim_duration.setter
    def anim_duration(self, v: int):
        self._data["anim_duration"] = max(80, min(600, v)); self._save()

    # display_name / email 은 하위호환용 alias
    @property
    def display_name(self) -> str:
        return self.app_username

    @property
    def email(self) -> str:
        return self.app_password
