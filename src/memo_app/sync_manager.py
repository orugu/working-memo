from __future__ import annotations

import threading
from datetime import datetime

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from .db import DatabaseManager, TodoCRUD, UserCRUD
from .settings_manager import SettingsManager
from .todo_manager import TodoManager


class SyncState:
    OFFLINE    = "offline"
    SYNCING    = "syncing"
    SYNCED     = "synced"
    PENDING    = "pending"
    AUTH_ERROR = "auth_error"


class _Worker(QRunnable):
    """백그라운드 스레드에서 fn() 실행. UI 블로킹 없음."""

    def __init__(self, fn):
        super().__init__()
        self._fn = fn
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        try:
            self._fn()
        except Exception as e:
            print(f"[SyncWorker] 예외: {e}")


class SyncManager(QObject):
    status_changed  = Signal(str)   # SyncState 상수 — Qt가 자동으로 메인 스레드에 큐잉
    todos_refreshed = Signal()

    _RETRY_MS = 30_000  # 30초

    def __init__(
        self,
        db: DatabaseManager,
        settings: SettingsManager,
        todo_manager: TodoManager,
        parent=None,
    ):
        super().__init__(parent)
        self._db       = db
        self._settings = settings
        self._tm       = todo_manager
        self._user_id: int | None = None
        self._state    = SyncState.OFFLINE
        self._lock     = threading.Lock()  # 동시 sync 방지

        self._timer = QTimer(self)
        self._timer.setInterval(self._RETRY_MS)
        self._timer.timeout.connect(self._schedule_sync)

    # ── 공개 API ──────────────────────────────────────────────────────────

    def start(self):
        self._schedule_sync()
        self._timer.start()

    def push_now(self):
        """로컬 변경 직후 즉시 push 시도 (비블로킹)."""
        if self._state in (SyncState.SYNCED, SyncState.PENDING):
            QThreadPool.globalInstance().start(_Worker(self._push_pending))

    @property
    def state(self) -> str:
        return self._state

    # ── 내부 스케줄링 ─────────────────────────────────────────────────────

    def _schedule_sync(self):
        """메인 스레드에서 호출 — 실제 작업은 스레드풀에서."""
        QThreadPool.globalInstance().start(_Worker(self._try_sync))

    # ── 동기화 작업 (백그라운드 스레드) ───────────────────────────────────

    def _try_sync(self):
        if not self._lock.acquire(blocking=False):
            return  # 이미 sync 중
        try:
            self._do_sync()
        finally:
            self._lock.release()

    def _do_sync(self):
        app_user = self._settings.app_username
        app_pw   = self._settings.app_password

        if not app_user or not app_pw:
            self._emit_state(SyncState.OFFLINE)
            return

        self._emit_state(SyncState.SYNCING)

        # 1. DB 연결 — 내부 IP 우선, 실패 시 외부 호스트 fallback
        if not self._db.is_connected:
            try:
                hosts = [
                    self._settings.db_host_internal,
                    self._settings.db_host,
                ]
                self._db.connect_any(
                    hosts=hosts,
                    db_port=self._settings.db_port,
                    username=self._settings.db_username,
                    password=self._settings.db_password,
                    db_name=self._settings.db_name,
                )
            except Exception as e:
                print(f"[Sync] 연결 실패: {e}")
                self._emit_state(SyncState.OFFLINE)
                return

        # 2. 앱 사용자 인증 (users 테이블)
        try:
            with self._db.session() as s:
                user, created = UserCRUD.get_or_create(s, app_user, app_pw)
                self._user_id = user.id
                print(f"[Sync] {'신규 계정' if created else '로그인'}: {app_user} (id={user.id})")
        except ValueError as e:
            print(f"[Sync] 인증 오류: {e}")
            self._emit_state(SyncState.AUTH_ERROR)
            return
        except Exception as e:
            print(f"[Sync] 세션 오류: {e}")
            self._db._reset()
            self._emit_state(SyncState.OFFLINE)
            return

        # 3. DB → 로컬 pull
        try:
            with self._db.session() as s:
                db_todos = TodoCRUD.get_all(s, self._user_id)
            self._tm.merge_from_db([_to_dict(t) for t in db_todos])
            self.todos_refreshed.emit()
        except Exception as e:
            print(f"[Sync] Pull 실패: {e}")

        # 4. 로컬 → DB push
        self._push_pending()

    def _push_pending(self):
        if self._user_id is None or not self._db.is_connected:
            self._emit_state(SyncState.PENDING)
            return

        pending = self._tm.get_pending()
        if not pending:
            self._emit_state(SyncState.SYNCED)
            return

        self._emit_state(SyncState.SYNCING)
        synced_ids: set[str] = set()
        try:
            with self._db.session() as s:
                for todo in pending:
                    TodoCRUD.upsert(
                        s,
                        todo_id=todo.id,
                        user_id=self._user_id,
                        text=todo.text,
                        completed=todo.completed,
                        completed_at=_parse_dt(todo.completed_at),
                        created_at=_parse_dt(todo.created_at) or datetime.utcnow(),
                        updated_at=_parse_dt(todo.updated_at) or datetime.utcnow(),
                        deleted=todo.deleted,
                        parent_id=todo.parent_id,
                    )
                    synced_ids.add(todo.id)
            self._tm.mark_synced(synced_ids)
            self.todos_refreshed.emit()
            self._emit_state(SyncState.SYNCED)
            print(f"[Sync] {len(synced_ids)}개 push 완료")
        except Exception as e:
            print(f"[Sync] Push 실패: {e}")
            self._db._reset()
            self._emit_state(SyncState.PENDING)

    def _emit_state(self, state: str):
        if self._state != state:
            self._state = state
            self.status_changed.emit(state)  # Qt가 메인 스레드에 자동 큐잉


# ── 유틸 ──────────────────────────────────────────────────────────────────────

def _parse_dt(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None


def _to_dict(t) -> dict:
    def iso(dt) -> str | None:
        return dt.isoformat() if dt else None
    return {
        "id": t.id,
        "text": t.text,
        "created_at": iso(t.created_at),
        "updated_at": iso(t.updated_at),
        "completed_at": iso(t.completed_at),
        "completed": t.completed,
        "deleted": t.deleted,
        "parent_id": getattr(t, "parent_id", None),
    }
