import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from platformdirs import user_data_dir


class Todo:
    def __init__(
        self,
        text: str,
        id: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        completed_at: str | None = None,
        completed: bool = False,
        synced: bool = False,
        deleted: bool = False,
    ):
        self.id = id or str(uuid.uuid4())
        self.text = text
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()
        self.completed_at = completed_at
        self.completed = completed
        self.synced = synced
        self.deleted = deleted

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "completed": self.completed,
            "synced": self.synced,
            "deleted": self.deleted,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Todo":
        return cls(
            id=d.get("id"),
            text=d.get("text", ""),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            completed_at=d.get("completed_at"),
            completed=d.get("completed", False),
            synced=d.get("synced", False),
            deleted=d.get("deleted", False),
        )


class TodoManager:
    def __init__(self):
        data_dir = Path(user_data_dir("WorkingMemo", "WorkingMemo"))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "todos.json"
        self._todos: list[Todo] = []
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self._todos = [Todo.from_dict(d) for d in data]
            except Exception:
                self._todos = []

    def _save(self):
        # deleted+synced 항목은 이미 DB에 반영됐으므로 로컬에서 제거
        self._todos = [t for t in self._todos if not (t.deleted and t.synced)]
        self.path.write_text(
            json.dumps([t.to_dict() for t in self._todos], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _touch(self, todo: Todo):
        todo.updated_at = datetime.utcnow().isoformat()
        todo.synced = False

    # ── 쓰기 ─────────────────────────────────────────────────────────────

    def add(self, text: str) -> Todo:
        with self._lock:
            todo = Todo(text=text.strip())
            self._todos.append(todo)
            self._save()
            return todo

    def toggle_complete(self, todo_id: str) -> Todo | None:
        with self._lock:
            for todo in self._todos:
                if todo.id == todo_id:
                    todo.completed = not todo.completed
                    todo.completed_at = datetime.utcnow().isoformat() if todo.completed else None
                    self._touch(todo)
                    self._save()
                    return todo
        return None

    def delete(self, todo_id: str):
        with self._lock:
            for todo in self._todos:
                if todo.id == todo_id:
                    todo.deleted = True
                    self._touch(todo)
                    self._save()
                    return

    def delete_completed(self):
        with self._lock:
            for todo in self._todos:
                if todo.completed and not todo.deleted:
                    todo.deleted = True
                    self._touch(todo)
            self._save()

    def delete_all(self):
        with self._lock:
            for todo in self._todos:
                if not todo.deleted:
                    todo.deleted = True
                    self._touch(todo)
            self._save()

    # ── 읽기 ─────────────────────────────────────────────────────────────

    def get_all(self) -> list[Todo]:
        with self._lock:
            return [t for t in self._todos if not t.deleted]

    def get_pending(self) -> list[Todo]:
        with self._lock:
            return [t for t in self._todos if not t.synced]

    # ── 동기화 지원 ───────────────────────────────────────────────────────

    def mark_synced(self, todo_ids: set[str]):
        with self._lock:
            for todo in self._todos:
                if todo.id in todo_ids:
                    todo.synced = True
            self._save()  # _save() 내부에서 deleted+synced 정리

    def merge_from_db(self, db_todos: list[dict]):
        """DB에서 가져온 최신 데이터를 로컬과 병합. updated_at 기준 최신 우선."""
        with self._lock:
            self._merge(db_todos)

    def _merge(self, db_todos: list[dict]):
        local_map = {t.id: t for t in self._todos}
        for d in db_todos:
            tid = d["id"]
            db_updated = d.get("updated_at") or ""
            if tid not in local_map:
                # 로컬에 없으면 DB 항목 추가
                todo = Todo.from_dict({**d, "synced": True})
                self._todos.append(todo)
            else:
                local = local_map[tid]
                local_updated = local.updated_at or ""
                if not local.synced and local_updated >= db_updated:
                    # 로컬 변경이 더 최신 → 그대로 유지 (push 대상)
                    pass
                else:
                    # DB가 더 최신이거나 로컬이 이미 synced → DB로 덮어쓰기
                    local.text = d["text"]
                    local.completed = d["completed"]
                    local.completed_at = d.get("completed_at")
                    local.updated_at = d.get("updated_at") or local.updated_at
                    local.deleted = d.get("deleted", False)
                    local.synced = True
        self.path.write_text(
            json.dumps([t.to_dict() for t in self._todos], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
