from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from .models import Todo, User


class UserCRUD:
    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def get_or_create(session: Session, username: str, password: str) -> tuple[User, bool]:
        """(user, created) 반환. 비밀번호 불일치 시 ValueError."""
        user = session.query(User).filter_by(username=username).first()
        if user is None:
            user = User(
                username=username,
                password_hash=UserCRUD._hash(password),
                created_at=datetime.utcnow(),
            )
            session.add(user)
            session.flush()
            return user, True
        if user.password_hash != UserCRUD._hash(password):
            raise ValueError("비밀번호가 일치하지 않습니다.")
        return user, False

    @staticmethod
    def authenticate(session: Session, username: str, password: str) -> User | None:
        user = session.query(User).filter_by(username=username).first()
        if user and user.password_hash == UserCRUD._hash(password):
            return user
        return None


class TodoCRUD:
    @staticmethod
    def get_all(session: Session, user_id: int) -> list[Todo]:
        return (
            session.query(Todo)
            .filter(Todo.user_id == user_id, Todo.deleted == False)  # noqa: E712
            .order_by(Todo.created_at)
            .all()
        )

    @staticmethod
    def get_by_id(session: Session, todo_id: str) -> Todo | None:
        return session.get(Todo, todo_id)

    @staticmethod
    def upsert(
        session: Session,
        *,
        todo_id: str,
        user_id: int,
        text: str,
        completed: bool,
        completed_at: datetime | None,
        created_at: datetime,
        updated_at: datetime,
        deleted: bool,
    ) -> Todo:
        """로컬 레코드를 DB에 삽입하거나 updated_at 기준으로 병합."""
        todo = session.get(Todo, todo_id)
        if todo is None:
            todo = Todo(id=todo_id, user_id=user_id, created_at=created_at)
            session.add(todo)
            should_update = True
        else:
            # DB보다 로컬이 더 최신이면 덮어쓴다
            should_update = updated_at >= (todo.updated_at or datetime.min)

        if should_update:
            todo.text = text
            todo.completed = completed
            todo.completed_at = completed_at
            todo.updated_at = updated_at
            todo.deleted = deleted
        session.flush()
        return todo

    @staticmethod
    def soft_delete(session: Session, todo_id: str) -> bool:
        todo = session.get(Todo, todo_id)
        if todo is None:
            return False
        todo.deleted = True
        todo.updated_at = datetime.utcnow()
        session.flush()
        return True

    @staticmethod
    def delete_completed(session: Session, user_id: int) -> int:
        todos = (
            session.query(Todo)
            .filter(Todo.user_id == user_id, Todo.completed == True)  # noqa: E712
            .all()
        )
        for t in todos:
            t.deleted = True
            t.updated_at = datetime.utcnow()
        session.flush()
        return len(todos)

    @staticmethod
    def delete_all(session: Session, user_id: int) -> int:
        todos = session.query(Todo).filter(Todo.user_id == user_id).all()
        for t in todos:
            t.deleted = True
            t.updated_at = datetime.utcnow()
        session.flush()
        return len(todos)
