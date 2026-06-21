from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from platformdirs import user_data_dir
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


class DatabaseManager:
    """
    SQLite (로컬 fallback) 또는 PostgreSQL 연결 매니저.
    - is_connected 는 DB 쿼리 없이 플래그만 확인한다 (블로킹 없음).
    - connect() 실패 시 엔진을 완전히 리셋한다.
    """

    def __init__(self):
        self._engine: Engine | None = None
        self._Session: sessionmaker | None = None
        self._connected: bool = False

    # ── 연결 ──────────────────────────────────────────────────────────────

    def connect(
        self,
        *,
        db_host: str = "",
        db_port: str = "5432",
        username: str = "",
        password: str = "",
        db_name: str = "working_memo",
    ) -> None:
        self._reset()
        url = self._build_url(
            db_host=db_host,
            db_port=db_port,
            username=username,
            password=password,
            db_name=db_name,
        )
        connect_args = {} if not db_host else {"connect_timeout": 5}
        engine = create_engine(url, echo=False, connect_args=connect_args)
        Base.metadata.create_all(engine)
        self._engine = engine
        self._Session = sessionmaker(bind=engine, expire_on_commit=False)
        self._connected = True

    def connect_any(
        self,
        *,
        hosts: list[str],
        db_port: str = "5432",
        username: str = "",
        password: str = "",
        db_name: str = "working_memo",
    ) -> str:
        """hosts 순서대로 연결 시도, 성공한 호스트 반환."""
        last_exc: Exception | None = None
        for host in hosts:
            if not host:
                continue
            try:
                self.connect(
                    db_host=host,
                    db_port=db_port,
                    username=username,
                    password=password,
                    db_name=db_name,
                )
                print(f"[DB] 연결 성공: {host}:{db_port}")
                return host
            except Exception as e:
                print(f"[DB] {host}:{db_port} 실패: {e}")
                last_exc = e
        raise last_exc or RuntimeError("연결할 호스트가 없습니다.")

    def disconnect(self) -> None:
        self._reset()

    def _reset(self) -> None:
        self._connected = False
        if self._engine:
            try:
                self._engine.dispose()
            except Exception:
                pass
        self._engine = None
        self._Session = None

    @property
    def is_connected(self) -> bool:
        """DB 쿼리 없이 플래그만 반환 — 블로킹 없음."""
        return self._connected and self._Session is not None

    # ── 세션 컨텍스트 매니저 ────────────────────────────────────────────────

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if not self._Session:
            raise RuntimeError("DB에 연결되어 있지 않습니다.")
        sess: Session = self._Session()
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            # 연결이 끊어진 경우 상태 리셋
            self._connected = False
            raise
        finally:
            sess.close()

    # ── URL 빌더 ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_url(*, db_host, db_port, username, password, db_name) -> str:
        if not db_host:
            data_dir = Path(user_data_dir("WorkingMemo", "WorkingMemo"))
            data_dir.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{data_dir / 'memoapp.db'}"
        port = db_port or "40916"
        user = username or "postgres"
        return f"postgresql+psycopg2://{user}:{password}@{db_host}:{port}/{db_name}"
