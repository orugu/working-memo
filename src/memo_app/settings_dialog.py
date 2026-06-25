from PySide6.QtCore import QObject, QPoint, QRunnable, QThreadPool, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from memo_app import __version__
from .settings_manager import SettingsManager
from .updater import UpdateChecker

# ── Styles ──────────────────────────────────────────────────────────────────

_DIALOG_STYLE = """
QFrame#dialog {
    background-color: rgba(14, 14, 24, 252);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 28);
}
"""

_SIDEBAR_STYLE = """
QFrame#sidebar {
    background-color: rgba(255, 255, 255, 6);
    border-radius: 12px;
}
"""

_TAB_DEFAULT = """
QPushButton {
    background: transparent;
    color: rgba(255,255,255,130);
    border: none;
    border-radius: 8px;
    font-size: 13px;
    padding: 10px 14px;
    text-align: left;
}
QPushButton:hover { background: rgba(255,255,255,12); color: rgba(255,255,255,200); }
"""

_TAB_ACTIVE = """
QPushButton {
    background: rgba(100,160,255,180);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    padding: 10px 14px;
    text-align: left;
    font-weight: bold;
}
"""

_INPUT_STYLE = """
QLineEdit {
    background-color: rgba(255, 255, 255, 14);
    border: 1px solid rgba(255, 255, 255, 30);
    border-radius: 8px;
    color: rgba(255, 255, 255, 220);
    padding: 9px 12px;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: rgba(100, 160, 255, 190);
    background-color: rgba(255, 255, 255, 20);
}
"""

_SAVE_BTN_STYLE = """
QPushButton {
    background-color: rgba(100, 160, 255, 200);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    padding: 9px 24px;
}
QPushButton:hover { background-color: rgba(120, 180, 255, 220); }
QPushButton:pressed { background-color: rgba(80, 140, 230, 220); }
"""

_DANGER_BTN_STYLE = """
QPushButton {
    background-color: rgba(220, 60, 60, 180);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    padding: 9px 24px;
}
QPushButton:hover { background-color: rgba(240, 80, 80, 220); }
QPushButton:pressed { background-color: rgba(200, 40, 40, 220); }
"""

_CLOSE_BTN_STYLE = """
QPushButton {
    background: rgba(255,255,255,14);
    color: rgba(255,255,255,140);
    border: none;
    border-radius: 12px;
    font-size: 12px;
}
QPushButton:hover { background: #e05050; color: white; }
"""

_SLIDER_STYLE = """
QSlider::groove:horizontal {
    height: 4px;
    background: rgba(255,255,255,25);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 18px; height: 18px;
    margin: -7px 0;
    border-radius: 9px;
    background: rgba(100,160,255,230);
}
QSlider::sub-page:horizontal {
    background: rgba(100,160,255,150);
    border-radius: 2px;
}
"""

_SECTION_TITLE = "color: rgba(255,255,255,110); font-size: 11px; font-weight: bold; letter-spacing: 1px;"
_FIELD_LABEL   = "color: rgba(255,255,255,170); font-size: 13px;"
_HINT_LABEL    = "color: rgba(255,255,255,55); font-size: 11px;"
_VALUE_LABEL   = "color: rgba(100,160,255,220); font-size: 14px; font-weight: bold;"
_SUCCESS_LABEL = "color: rgba(100,210,120,200); font-size: 12px;"


def _divider() -> QFrame:
    d = QFrame()
    d.setFrameShape(QFrame.Shape.HLine)
    d.setMaximumHeight(1)
    d.setStyleSheet("background: rgba(255,255,255,15); border: none;")
    return d


def _section(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(_SECTION_TITLE)
    return lbl


def _label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_FIELD_LABEL)
    return lbl


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_HINT_LABEL)
    lbl.setWordWrap(True)
    return lbl


# ── Tab pages ────────────────────────────────────────────────────────────────

class _AccessPage(QWidget):
    """접속정보 탭"""

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # ── DB 서버 (PostgreSQL 접속) ──────────────────────────────────────
        lay.addWidget(_section("DB 서버 접속"))
        lay.addWidget(_divider())

        host_row = QHBoxLayout()
        host_row.setSpacing(8)

        host_col = QVBoxLayout()
        host_col.setSpacing(3)
        host_col.addWidget(_label("Host"))
        self._host = self._input(settings.db_host, "devlovers.cloud")
        host_col.addWidget(self._host)

        port_col = QVBoxLayout()
        port_col.setSpacing(3)
        port_col.addWidget(_label("Port"))
        self._port = self._input(settings.db_port, "40916")
        self._port.setFixedWidth(80)
        port_col.addWidget(self._port)

        host_row.addLayout(host_col, 1)
        host_row.addLayout(port_col)
        lay.addLayout(host_row)

        lay.addWidget(_label("DB Name"))
        self._dbname = self._input(settings.db_name, "working_memo")
        lay.addWidget(self._dbname)

        db_cred_row = QHBoxLayout()
        db_cred_row.setSpacing(8)

        db_user_col = QVBoxLayout()
        db_user_col.setSpacing(3)
        db_user_col.addWidget(_label("DB Username"))
        self._db_user = self._input(settings.db_username, "postgres")
        db_user_col.addWidget(self._db_user)

        db_pw_col = QVBoxLayout()
        db_pw_col.setSpacing(3)
        db_pw_col.addWidget(_label("DB Password"))
        self._db_pw = self._input(settings.db_password, "")
        self._db_pw.setEchoMode(QLineEdit.EchoMode.Password)
        db_pw_col.addWidget(self._db_pw)

        db_cred_row.addLayout(db_user_col, 1)
        db_cred_row.addLayout(db_pw_col, 1)
        lay.addLayout(db_cred_row)

        # 연결 테스트 버튼
        test_btn = QPushButton("연결 테스트 및 테이블 생성")
        test_btn.setStyleSheet(_SAVE_BTN_STYLE)
        test_btn.setFixedHeight(36)
        test_btn.clicked.connect(self._test_connection)
        lay.addWidget(test_btn)

        self._conn_msg = QLabel("")
        self._conn_msg.setStyleSheet(_SUCCESS_LABEL)
        self._conn_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._conn_msg.setWordWrap(True)
        lay.addWidget(self._conn_msg)

        lay.addSpacing(4)

        # ── 앱 계정 (Working Memo 사용자) ─────────────────────────────────
        lay.addWidget(_section("앱 계정"))
        lay.addWidget(_divider())
        lay.addWidget(_hint("이 ID/Password로 할 일 목록이 분리 관리됩니다."))

        lay.addWidget(_label("ID"))
        self._id = self._input(settings.app_username, "사용할 ID")
        lay.addWidget(self._id)

        lay.addWidget(_label("Password"))
        self._pw = self._input(settings.app_password, "비밀번호")
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self._pw)

        save_btn = QPushButton("저장")
        save_btn.setStyleSheet(_SAVE_BTN_STYLE)
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._save)
        lay.addWidget(save_btn)

        self._msg = QLabel("")
        self._msg.setStyleSheet(_SUCCESS_LABEL)
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._msg)

        lay.addStretch()

    @staticmethod
    def _input(value: str, placeholder: str) -> QLineEdit:
        w = QLineEdit(value)
        w.setPlaceholderText(placeholder)
        w.setStyleSheet(_INPUT_STYLE)
        w.setFixedHeight(36)
        return w

    def _save(self):
        self.settings.db_host     = self._host.text().strip()
        self.settings.db_port     = self._port.text().strip() or "40916"
        self.settings.db_name     = self._dbname.text().strip() or "working_memo"
        self.settings.db_username = self._db_user.text().strip()
        self.settings.db_password = self._db_pw.text().strip()
        self.settings.app_username = self._id.text().strip()
        self.settings.app_password = self._pw.text().strip()
        self._msg.setText("저장됐습니다 ✓")
        QTimer.singleShot(2500, lambda: self._msg.setText(""))

    def _test_connection(self):
        self._conn_msg.setStyleSheet(_SUCCESS_LABEL)
        self._conn_msg.setText("연결 중...")

        host    = self._host.text().strip()
        port    = self._port.text().strip() or "40916"
        db_name = self._dbname.text().strip() or "working_memo"
        db_user = self._db_user.text().strip()
        db_pw   = self._db_pw.text().strip()

        # Signal로 스레드 → 메인스레드 안전하게 전달
        class _Bridge(QObject):
            result = Signal(bool, str)

        bridge = _Bridge(self)
        bridge.result.connect(self._on_test_result)

        class _Worker(QRunnable):
            def __init__(self_, b):
                super().__init__()
                self_._b = b
                self_.setAutoDelete(True)

            @Slot()
            def run(self_):
                from .db import DatabaseManager
                db = DatabaseManager()
                try:
                    db.connect(
                        db_host=host, db_port=port,
                        username=db_user, password=db_pw, db_name=db_name,
                    )
                    db.disconnect()
                    self_._b.result.emit(True, "연결 성공 — 테이블이 생성됐습니다 ✓")
                except Exception as e:
                    short = str(e).split("\n")[0][:120]
                    self_._b.result.emit(False, f"연결 실패: {short}")

        QThreadPool.globalInstance().start(_Worker(bridge))

    def _on_test_result(self, ok: bool, msg: str):
        color = _SUCCESS_LABEL if ok else "color: rgba(220,80,80,220); font-size: 12px;"
        self._conn_msg.setStyleSheet(color)
        self._conn_msg.setText(msg)


class _DisplayCard(QFrame):
    """디스플레이 하나의 코너 설정 카드."""
    changed = Signal()

    def __init__(self, idx: int, screen, config: dict):
        super().__init__()
        self._config = config
        self.setStyleSheet("""
QFrame {
    background: rgba(255,255,255,6);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,12);
}
""")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        geo = screen.geometry()
        is_primary = screen == QApplication.primaryScreen()
        suffix = "  [기본 디스플레이]" if is_primary else ""
        name_lbl = QLabel(f"디스플레이 {idx + 1}  —  {geo.width()} × {geo.height()} px{suffix}")
        name_lbl.setStyleSheet("color: rgba(255,255,255,210); font-size: 12px; font-weight: bold;")

        self._cb = QCheckBox("이 디스플레이에서 코너 감지 활성화")
        self._cb.setChecked(config.get("enabled", True))
        self._cb.setStyleSheet("""
QCheckBox { color: rgba(255,255,255,160); font-size: 12px; }
QCheckBox::indicator { width:14px; height:14px; border-radius:3px;
    border:1.5px solid rgba(255,255,255,100); background:transparent; }
QCheckBox::indicator:checked { background:#4caf50; border-color:#4caf50; }
""")
        self._cb.stateChanged.connect(self._on_cb)

        slider_row = QHBoxLayout()
        slider_row.addWidget(_label("코너 범위"))
        slider_row.addStretch()
        self._val_lbl = QLabel(f"{config.get('corner_size', 20)} px")
        self._val_lbl.setStyleSheet(_VALUE_LABEL)
        slider_row.addWidget(self._val_lbl)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(5, 100)
        self._slider.setValue(config.get("corner_size", 20))
        self._slider.setStyleSheet(_SLIDER_STYLE)
        self._slider.setEnabled(config.get("enabled", True))
        self._slider.valueChanged.connect(self._on_slider)

        lay.addWidget(name_lbl)
        lay.addWidget(self._cb)
        lay.addLayout(slider_row)
        lay.addWidget(self._slider)

    def _on_cb(self):
        self._config["enabled"] = self._cb.isChecked()
        self._slider.setEnabled(self._cb.isChecked())
        self.changed.emit()

    def _on_slider(self, v: int):
        self._val_lbl.setText(f"{v} px")
        self._config["corner_size"] = v
        self.changed.emit()

    def get_config(self) -> dict:
        return dict(self._config)


class _RangePage(QWidget):
    """범위설정 탭 — 디스플레이별 코너 인식 범위"""
    displays_changed = Signal()

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self._cards: list[_DisplayCard] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: rgba(255,255,255,8); width:5px; border-radius:2px; }
QScrollBar::handle:vertical { background: rgba(255,255,255,50); border-radius:2px; min-height:16px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
""")

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._lay = QVBoxLayout(inner)
        self._lay.setContentsMargins(0, 0, 4, 0)
        self._lay.setSpacing(10)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._build_cards()

    def _build_cards(self):
        while self._lay.count():
            item = self._lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        self._lay.addWidget(_section("디스플레이별 코너 인식 범위"))
        self._lay.addWidget(_divider())
        self._lay.addWidget(_hint(
            "각 디스플레이의 좌측 상단 코너에서 마우스 + Ctrl로 오버레이를 열 수 있습니다. "
            "범위가 클수록 더 넓은 영역에서 감지됩니다. (5 – 100 px)"
        ))

        screens = QApplication.screens()
        configs = list(self.settings.display_configs)
        while len(configs) < len(screens):
            configs.append({"corner_size": self.settings.corner_size, "enabled": True})

        for idx, screen in enumerate(screens):
            card = _DisplayCard(idx, screen, configs[idx])
            card.changed.connect(self._on_changed)
            self._lay.addWidget(card)
            self._cards.append(card)

        self._lay.addStretch()

    def _on_changed(self):
        new_configs = [c.get_config() for c in self._cards]
        self.settings.display_configs = new_configs
        self.displays_changed.emit()

    def refresh_screens(self):
        """디스플레이 구성이 바뀌었을 때 카드를 다시 구성한다."""
        self._build_cards()


class _HistoryPage(QWidget):
    """기록 관리 탭"""
    def __init__(self, settings: SettingsManager):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(_section("기록 관리"))
        lay.addWidget(_divider())

        lay.addWidget(_label("완료된 항목 관리"))
        lay.addWidget(_hint("완료 처리된 할 일 항목을 일괄 삭제합니다. 이 작업은 되돌릴 수 없습니다."))

        self._clear_btn = QPushButton("완료 항목 전체 삭제")
        self._clear_btn.setStyleSheet(_DANGER_BTN_STYLE)
        self._clear_btn.setFixedHeight(38)
        self._clear_btn.clicked.connect(self._clear_done)
        lay.addWidget(self._clear_btn)

        self._msg = QLabel("")
        self._msg.setStyleSheet(_SUCCESS_LABEL)
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._msg)

        lay.addSpacing(8)
        lay.addWidget(_divider())
        lay.addWidget(_label("모든 기록 초기화"))
        lay.addWidget(_hint("모든 할 일 항목을 삭제합니다. 이 작업은 되돌릴 수 없습니다."))

        self._reset_btn = QPushButton("전체 초기화")
        self._reset_btn.setStyleSheet(_DANGER_BTN_STYLE)
        self._reset_btn.setFixedHeight(38)
        self._reset_btn.clicked.connect(self._reset_all)
        lay.addWidget(self._reset_btn)

        lay.addStretch()

        self._todo_manager = None
        self._sync_manager = None

    def set_todo_manager(self, manager):
        self._todo_manager = manager

    def set_sync_manager(self, sync_manager):
        self._sync_manager = sync_manager

    def _clear_done(self):
        if not self._todo_manager:
            return
        self._todo_manager.delete_completed()
        if self._sync_manager:
            self._sync_manager.push_now()
        self._show_msg("완료 항목을 삭제했습니다 ✓")

    def _reset_all(self):
        if not self._todo_manager:
            return
        self._todo_manager.delete_all()
        if self._sync_manager:
            self._sync_manager.push_now()
        self._show_msg("전체 초기화됐습니다 ✓")

    def _show_msg(self, text: str):
        self._msg.setText(text)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2500, lambda: self._msg.setText(""))


_FILTER_BTN = """
QPushButton {
    background: rgba(255,255,255,12);
    color: rgba(255,255,255,140);
    border: none;
    border-radius: 6px;
    font-size: 11px;
    padding: 4px 10px;
}
QPushButton:hover { background: rgba(255,255,255,22); color: white; }
QPushButton:checked {
    background: rgba(100,160,255,200);
    color: white;
}
"""

_STATUS_STYLES = {
    "active":    ("●", "color: rgba(100,160,255,220);"),
    "completed": ("●", "color: rgba(100,210,120,220);"),
    "deleted":   ("●", "color: rgba(180,80,80,200);"),
}


def _log_item_widget(todo) -> QWidget:
    from datetime import datetime

    def _fmt(iso):
        if not iso:
            return ""
        try:
            return datetime.fromisoformat(iso).strftime("%y/%m/%d %H:%M")
        except Exception:
            return iso

    if todo.deleted:
        status_key = "deleted"
        status_text = "삭제됨"
    elif todo.completed:
        status_key = "completed"
        status_text = "완료"
    else:
        status_key = "active"
        status_text = "활성"

    dot_char, dot_style = _STATUS_STYLES[status_key]

    frame = QFrame()
    frame.setStyleSheet("""
QFrame {
    background: rgba(255,255,255,6);
    border-radius: 6px;
    border: 1px solid rgba(255,255,255,10);
}
""")
    row = QHBoxLayout(frame)
    row.setContentsMargins(10, 7, 10, 7)
    row.setSpacing(8)

    dot = QLabel(dot_char)
    dot.setStyleSheet(dot_style + " font-size: 9px;")
    dot.setFixedWidth(10)

    info_col = QVBoxLayout()
    info_col.setSpacing(2)

    text_style = "color: rgba(255,255,255,75); font-size: 12px; text-decoration: line-through;" if todo.deleted else (
        "color: rgba(255,255,255,80); font-size: 12px; text-decoration: line-through;" if todo.completed else
        "color: rgba(255,255,255,200); font-size: 12px;"
    )

    indent = "  └ " if todo.parent_id else ""
    text_lbl = QLabel(f"{indent}{todo.text}")
    text_lbl.setStyleSheet(text_style)
    text_lbl.setWordWrap(True)

    meta_parts = [f"추가 {_fmt(todo.created_at)}"]
    if todo.completed and todo.completed_at:
        meta_parts.append(f"완료 {_fmt(todo.completed_at)}")
    if todo.deleted:
        meta_parts.append(f"삭제 {_fmt(todo.updated_at)}")

    meta_lbl = QLabel("  •  ".join(meta_parts))
    meta_lbl.setStyleSheet("color: rgba(255,255,255,50); font-size: 10px;")

    status_lbl = QLabel(status_text)
    status_lbl.setStyleSheet(dot_style + " font-size: 10px; font-weight: bold;")
    status_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
    status_lbl.setFixedWidth(36)

    info_col.addWidget(text_lbl)
    info_col.addWidget(meta_lbl)

    row.addWidget(dot)
    row.addLayout(info_col, 1)
    row.addWidget(status_lbl)

    return frame


class _LogPage(QWidget):
    """전체 기록 탭 — 삭제된 항목 포함 전체 히스토리"""

    def __init__(self):
        super().__init__()
        self._todo_manager = None
        self._filter = "all"  # all | active | completed | deleted

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        lay.addWidget(_section("전체 기록"))
        lay.addWidget(_divider())

        # ── 필터 버튼 ────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)

        self._filter_btns: dict[str, QPushButton] = {}
        for key, label in [("all", "전체"), ("active", "활성"), ("completed", "완료"), ("deleted", "삭제됨")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(_FILTER_BTN)
            btn.clicked.connect(lambda _, k=key: self._set_filter(k))
            filter_row.addWidget(btn)
            self._filter_btns[key] = btn

        self._filter_btns["all"].setChecked(True)
        filter_row.addStretch()

        refresh_btn = QPushButton("↺")
        refresh_btn.setFixedSize(26, 26)
        refresh_btn.setStyleSheet(_FILTER_BTN)
        refresh_btn.setToolTip("새로고침")
        refresh_btn.clicked.connect(self.refresh)
        filter_row.addWidget(refresh_btn)

        lay.addLayout(filter_row)

        # ── 스크롤 영역 ──────────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: rgba(255,255,255,8); width:5px; border-radius:2px; }
QScrollBar::handle:vertical { background: rgba(255,255,255,50); border-radius:2px; min-height:16px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
""")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._inner_lay = QVBoxLayout(self._inner)
        self._inner_lay.setContentsMargins(0, 0, 4, 0)
        self._inner_lay.setSpacing(4)
        self._inner_lay.addStretch()
        self._scroll.setWidget(self._inner)

        self._empty_lbl = QLabel("기록이 없습니다.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet("color: rgba(255,255,255,50); font-size: 13px; padding: 24px 0;")
        self._empty_lbl.hide()

        lay.addWidget(self._empty_lbl)
        lay.addWidget(self._scroll, 1)

    def set_todo_manager(self, manager):
        self._todo_manager = manager

    def _set_filter(self, key: str):
        self._filter = key
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
        self.refresh()

    def refresh(self):
        if not self._todo_manager:
            return

        all_todos = self._todo_manager.get_history()

        if self._filter == "active":
            todos = [t for t in all_todos if not t.deleted and not t.completed]
        elif self._filter == "completed":
            todos = [t for t in all_todos if not t.deleted and t.completed]
        elif self._filter == "deleted":
            todos = [t for t in all_todos if t.deleted]
        else:
            todos = all_todos

        while self._inner_lay.count() > 1:
            item = self._inner_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not todos:
            self._empty_lbl.show()
            self._scroll.hide()
        else:
            self._empty_lbl.hide()
            self._scroll.show()
            for todo in todos:
                w = _log_item_widget(todo)
                self._inner_lay.insertWidget(self._inner_lay.count() - 1, w)


_PILL_ON = """
QPushButton {
    background: rgba(100,160,255,200); color: white;
    border: none; border-radius: 6px; font-size: 12px; padding: 5px 10px;
}"""
_PILL_OFF = """
QPushButton {
    background: rgba(255,255,255,12); color: rgba(255,255,255,140);
    border: 1px solid rgba(255,255,255,25); border-radius: 6px;
    font-size: 12px; padding: 5px 10px;
}
QPushButton:hover { background: rgba(255,255,255,22); color: rgba(255,255,255,200); }"""


class _UIPage(QWidget):
    """UI 설정 탭"""

    trigger_changed = Signal(str, str)  # (trigger_mode, quick_key)

    def __init__(self, settings: SettingsManager):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self._settings = settings

        # ── 트리거 설정 ───────────────────────────────────────────────────
        lay.addWidget(_section("트리거 설정"))
        lay.addWidget(_divider())

        # 트리거 모드 선택
        lay.addWidget(_label("트리거 방식"))
        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self._mode_grp = QButtonGroup(self)
        self._mode_grp.setExclusive(True)
        for label, val in [("📐  코너 + 키", "corner_key"), ("⌨️  키만 누르기", "key_only")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(settings.trigger_mode == val)
            btn.setProperty("val", val)
            btn.setStyleSheet(_PILL_ON if settings.trigger_mode == val else _PILL_OFF)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._mode_grp.addButton(btn)
            mode_row.addWidget(btn)
        mode_row.addStretch()
        lay.addLayout(mode_row)
        lay.addWidget(_hint("코너 + 키: 마우스를 코너에 놓고 키 입력 시 열기/닫기\n키만 누르기: 마우스 위치 관계없이 키 입력만으로 열기/닫기"))

        lay.addSpacing(6)

        # 트리거 키 선택
        lay.addWidget(_label("트리거 키"))
        key_rows = [
            [("Ctrl", "ctrl"), ("Alt", "alt"), ("Shift", "shift"), ("Cmd ⌘", "cmd")],
            [("F1","f1"),("F2","f2"),("F3","f3"),("F4","f4"),("F5","f5"),("F6","f6")],
            [("F7","f7"),("F8","f8"),("F9","f9"),("F10","f10"),("F11","f11"),("F12","f12")],
        ]
        self._key_grp = QButtonGroup(self)
        self._key_grp.setExclusive(True)
        for row_items in key_rows:
            row = QHBoxLayout()
            row.setSpacing(4)
            for label, val in row_items:
                btn = QPushButton(label)
                btn.setCheckable(True)
                btn.setChecked(settings.quick_key == val)
                btn.setProperty("val", val)
                btn.setStyleSheet(_PILL_ON if settings.quick_key == val else _PILL_OFF)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setFixedHeight(28)
                self._key_grp.addButton(btn)
                row.addWidget(btn)
            row.addStretch()
            lay.addLayout(row)

        self._mode_grp.buttonClicked.connect(self._on_trigger_change)
        self._key_grp.buttonClicked.connect(self._on_trigger_change)

        lay.addSpacing(8)

        lay.addWidget(_section("UI 설정"))
        lay.addWidget(_divider())

        row = QHBoxLayout()
        row.addWidget(_label("오버레이 너비"))
        row.addStretch()
        self._width_val = QLabel(f"{settings._data.get('overlay_width', 380)} px")
        self._width_val.setStyleSheet(_VALUE_LABEL)
        row.addWidget(self._width_val)
        lay.addLayout(row)

        self._width_slider = QSlider(Qt.Orientation.Horizontal)
        self._width_slider.setRange(280, 600)
        self._width_slider.setValue(settings._data.get("overlay_width", 380))
        self._width_slider.setStyleSheet(_SLIDER_STYLE)
        self._width_slider.valueChanged.connect(self._on_width)
        lay.addWidget(self._width_slider)
        lay.addWidget(_hint("오버레이 창의 너비를 조정합니다. (280 – 600 px)"))

        lay.addSpacing(8)

        row2 = QHBoxLayout()
        row2.addWidget(_label("닫힘 지연 시간"))
        row2.addStretch()
        self._delay_val = QLabel(f"{settings._data.get('leave_delay', 400)} ms")
        self._delay_val.setStyleSheet(_VALUE_LABEL)
        row2.addWidget(self._delay_val)
        lay.addLayout(row2)

        self._delay_slider = QSlider(Qt.Orientation.Horizontal)
        self._delay_slider.setRange(100, 2000)
        self._delay_slider.setValue(settings._data.get("leave_delay", 400))
        self._delay_slider.setStyleSheet(_SLIDER_STYLE)
        self._delay_slider.valueChanged.connect(self._on_delay)
        lay.addWidget(self._delay_slider)
        lay.addWidget(_hint("마우스가 오버레이를 벗어난 후 창이 닫히기까지의 지연 시간입니다. (100 – 2000 ms)"))

        lay.addSpacing(8)

        # 애니메이션 활성화 체크박스
        anim_row = QHBoxLayout()
        anim_cb = QCheckBox("창 열기/닫기 애니메이션 사용")
        anim_cb.setChecked(settings.animation)
        anim_cb.setStyleSheet("""
QCheckBox { color: rgba(255,255,255,170); font-size: 13px; }
QCheckBox::indicator { width:16px; height:16px; border-radius:4px;
    border:2px solid rgba(255,255,255,120); background:transparent; }
QCheckBox::indicator:checked { background:#4caf50; border-color:#4caf50; }
""")
        anim_row.addWidget(anim_cb)
        anim_row.addStretch()
        lay.addLayout(anim_row)

        # 애니메이션 속도 슬라이더
        dur_row = QHBoxLayout()
        dur_row.addWidget(_label("애니메이션 속도"))
        dur_row.addStretch()
        self._dur_val = QLabel(f"{settings.anim_duration} ms")
        self._dur_val.setStyleSheet(_VALUE_LABEL)
        dur_row.addWidget(self._dur_val)
        lay.addLayout(dur_row)

        self._dur_slider = QSlider(Qt.Orientation.Horizontal)
        self._dur_slider.setRange(80, 600)
        self._dur_slider.setValue(settings.anim_duration)
        self._dur_slider.setStyleSheet(_SLIDER_STYLE)
        self._dur_slider.setEnabled(settings.animation)
        self._dur_slider.valueChanged.connect(self._on_dur)
        lay.addWidget(self._dur_slider)
        lay.addWidget(_hint("창이 나타나고 사라질 때의 애니메이션 지속 시간입니다. (80 – 600 ms)"))

        anim_cb.stateChanged.connect(lambda: self._on_anim(anim_cb.isChecked()))

        lay.addStretch()

        self.overlay_width_changed = None
        self.leave_delay_changed = None

    def _on_trigger_change(self, _btn=None):
        mode = next(
            (b.property("val") for b in self._mode_grp.buttons() if b.isChecked()),
            self._settings.trigger_mode,
        )
        key = next(
            (b.property("val") for b in self._key_grp.buttons() if b.isChecked()),
            self._settings.quick_key,
        )
        for b in self._mode_grp.buttons():
            b.setStyleSheet(_PILL_ON if b.isChecked() else _PILL_OFF)
        for b in self._key_grp.buttons():
            b.setStyleSheet(_PILL_ON if b.isChecked() else _PILL_OFF)
        self._settings.trigger_mode = mode
        self._settings.quick_key    = key
        self.trigger_changed.emit(mode, key)

    def _on_width(self, v: int):
        self._width_val.setText(f"{v} px")
        self._settings._data["overlay_width"] = v
        self._settings._save()
        if self.overlay_width_changed:
            self.overlay_width_changed(v)

    def _on_delay(self, v: int):
        self._delay_val.setText(f"{v} ms")
        self._settings._data["leave_delay"] = v
        self._settings._save()
        if self.leave_delay_changed:
            self.leave_delay_changed(v)

    def _on_anim(self, enabled: bool):
        self._settings.animation = enabled
        self._dur_slider.setEnabled(enabled)

    def _on_dur(self, v: int):
        self._dur_val.setText(f"{v} ms")
        self._settings.anim_duration = v


# ── Main dialog ───────────────────────────────────────────────────────────────

_PROGRESS_STYLE = """
QProgressBar {
    background: rgba(255,255,255,14);
    border: 1px solid rgba(255,255,255,25);
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: rgba(100,160,255,200);
    border-radius: 4px;
}
"""


class _UpdatePage(QWidget):
    """버전 정보 및 업데이트 탭"""

    def __init__(self, checker: UpdateChecker):
        super().__init__()
        self._checker = checker
        self._download_url: str | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(_section("버전 정보"))
        lay.addWidget(_divider())

        ver_row = QHBoxLayout()
        ver_row.addWidget(_label("현재 버전"))
        ver_row.addStretch()
        self._ver_lbl = QLabel(f"v{__version__}")
        self._ver_lbl.setStyleSheet(_VALUE_LABEL)
        ver_row.addWidget(self._ver_lbl)
        lay.addLayout(ver_row)

        lay.addSpacing(4)
        lay.addWidget(_section("업데이트"))
        lay.addWidget(_divider())

        self._status_lbl = QLabel("업데이트 확인 전")
        self._status_lbl.setStyleSheet(_HINT_LABEL)
        self._status_lbl.setWordWrap(True)
        lay.addWidget(self._status_lbl)

        self._progress = QProgressBar()
        self._progress.setStyleSheet(_PROGRESS_STYLE)
        self._progress.setFixedHeight(8)
        self._progress.setRange(0, 100)
        self._progress.hide()
        lay.addWidget(self._progress)

        btn_row = QHBoxLayout()
        self._check_btn = QPushButton("업데이트 확인")
        self._check_btn.setStyleSheet(_SAVE_BTN_STYLE)
        self._check_btn.setFixedHeight(36)
        self._check_btn.clicked.connect(self._do_check)
        btn_row.addWidget(self._check_btn)

        self._install_btn = QPushButton("지금 업데이트")
        self._install_btn.setStyleSheet(_SAVE_BTN_STYLE)
        self._install_btn.setFixedHeight(36)
        self._install_btn.hide()
        self._install_btn.clicked.connect(self._do_install)
        btn_row.addWidget(self._install_btn)
        lay.addLayout(btn_row)

        lay.addStretch()

        checker.update_available.connect(self._on_update_available)
        checker.up_to_date.connect(self._on_up_to_date)
        checker.check_failed.connect(self._on_check_failed)
        checker.download_progress.connect(self._on_progress)
        checker.download_done.connect(self._on_download_done)
        checker.download_failed.connect(self._on_download_failed)

    def _do_check(self):
        self._check_btn.setEnabled(False)
        self._install_btn.hide()
        self._status_lbl.setStyleSheet(_HINT_LABEL)
        self._status_lbl.setText("확인 중...")
        self._checker.check_async()

    def _on_update_available(self, version: str, url: str):
        self._download_url = url
        self._status_lbl.setStyleSheet("color: rgba(100,210,120,200); font-size: 12px;")
        self._status_lbl.setText(f"새 버전 v{version}이 출시됐습니다!")
        self._install_btn.setText(f"v{version}으로 업데이트")
        self._install_btn.show()
        self._check_btn.setEnabled(True)

    def _on_up_to_date(self):
        self._status_lbl.setStyleSheet(_SUCCESS_LABEL)
        self._status_lbl.setText("최신 버전입니다 ✓")
        self._check_btn.setEnabled(True)

    def _on_check_failed(self, err: str):
        self._status_lbl.setStyleSheet("color: rgba(220,80,80,220); font-size: 12px;")
        self._status_lbl.setText(f"확인 실패: {err[:80]}")
        self._check_btn.setEnabled(True)

    def _do_install(self):
        if not self._download_url:
            return
        self._install_btn.setEnabled(False)
        self._check_btn.setEnabled(False)
        self._progress.setValue(0)
        self._progress.show()
        self._status_lbl.setText("다운로드 중...")
        self._checker.download_async(self._download_url)

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            self._progress.setRange(0, 100)
            self._progress.setValue(int(downloaded / total * 100))
        else:
            self._progress.setRange(0, 0)

    def _on_download_done(self, path: str):
        self._progress.hide()
        self._status_lbl.setText("업데이트 적용 중... 잠시 후 재시작됩니다.")
        QTimer.singleShot(800, lambda: self._checker.apply_update(path))

    def _on_download_failed(self, err: str):
        self._progress.hide()
        self._install_btn.setEnabled(True)
        self._check_btn.setEnabled(True)
        self._status_lbl.setStyleSheet("color: rgba(220,80,80,220); font-size: 12px;")
        self._status_lbl.setText(f"다운로드 실패: {err[:80]}")


class SettingsDialog(QWidget):
    displays_changed = Signal()
    trigger_changed  = Signal(str, str)  # (trigger_mode, quick_key)

    _TABS = [
        ("🔐", "접속정보"),
        ("🎯", "범위설정"),
        ("📋", "기록 관리"),
        ("📜", "전체 로그"),
        ("🎨", "UI 설정"),
        ("🔄", "업데이트"),
    ]

    def __init__(self, settings: SettingsManager, checker: UpdateChecker, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._checker = checker
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(520)
        self._tab_btns: list[QPushButton] = []
        self._first_show = True
        self._drag_pos: QPoint | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setObjectName("dialog")
        frame.setStyleSheet(_DIALOG_STYLE)
        root.addWidget(frame)

        outer = QVBoxLayout(frame)
        outer.setContentsMargins(20, 18, 20, 20)
        outer.setSpacing(16)

        # Header (드래그 영역)
        self._hdr_widget = QWidget()
        self._hdr_widget.setCursor(Qt.CursorShape.SizeAllCursor)
        hdr = QHBoxLayout(self._hdr_widget)
        hdr.setContentsMargins(0, 0, 0, 0)
        title = QLabel("⚙  설정")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(_CLOSE_BTN_STYLE)
        close_btn.setCursor(Qt.CursorShape.ArrowCursor)
        close_btn.clicked.connect(self.hide)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        outer.addWidget(self._hdr_widget)

        outer.addWidget(_divider())

        # Body: sidebar + content
        body = QHBoxLayout()
        body.setSpacing(16)
        body.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setStyleSheet(_SIDEBAR_STYLE)
        sidebar_frame.setFixedWidth(120)
        sidebar_lay = QVBoxLayout(sidebar_frame)
        sidebar_lay.setContentsMargins(8, 10, 8, 10)
        sidebar_lay.setSpacing(4)

        for i, (icon, label) in enumerate(self._TABS):
            btn = QPushButton(f"{icon}  {label}")
            btn.setStyleSheet(_TAB_DEFAULT)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._switch(idx))
            sidebar_lay.addWidget(btn)
            self._tab_btns.append(btn)

        sidebar_lay.addStretch()
        body.addWidget(sidebar_frame)

        # Content stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")

        self._page_access = _AccessPage(settings=self.settings)
        self._page_range = _RangePage(settings=self.settings)
        self._page_history = _HistoryPage(settings=self.settings)
        self._page_log = _LogPage()
        self._page_ui = _UIPage(settings=self.settings)
        self._page_update = _UpdatePage(checker=self._checker)

        self._page_range.displays_changed.connect(self.displays_changed)
        self._page_ui.trigger_changed.connect(self.trigger_changed)

        self._stack.addWidget(self._page_access)
        self._stack.addWidget(self._page_range)
        self._stack.addWidget(self._page_history)
        self._stack.addWidget(self._page_log)
        self._stack.addWidget(self._page_ui)
        self._stack.addWidget(self._page_update)

        self._stack.currentChanged.connect(self._on_tab_changed)

        body.addWidget(self._stack, 1)
        outer.addLayout(body)

        self._switch(0)

    def _switch(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.setStyleSheet(_TAB_ACTIVE if i == idx else _TAB_DEFAULT)

    def _on_tab_changed(self, idx: int):
        # 전체 로그 탭(index 3)으로 전환하면 즉시 새로고침
        if idx == 3:
            self._page_log.refresh()

    def set_todo_manager(self, manager):
        self._page_history.set_todo_manager(manager)
        self._page_log.set_todo_manager(manager)

    def set_sync_manager(self, sync_manager):
        self._page_history.set_sync_manager(sync_manager)

    def set_overlay_callbacks(self, on_width, on_delay):
        self._page_ui.overlay_width_changed = on_width
        self._page_ui.leave_delay_changed = on_delay

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            hdr_rect = self._hdr_widget.rect().translated(self._hdr_widget.pos())
            if hdr_rect.contains(event.position().toPoint()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def show_centered(self):
        self.adjustSize()
        if self._first_show:
            self._first_show = False
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
