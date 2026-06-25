import platform
from datetime import datetime

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .settings_dialog import SettingsDialog
from .settings_manager import SettingsManager
from .sync_manager import SyncState
from .todo_manager import Todo, TodoManager


def _fmt(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%m/%d %H:%M")
    except Exception:
        return iso


_CONTAINER_STYLE = """
QFrame#container {
    background-color: rgba(14, 14, 24, 238);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 28);
}
"""

_INPUT_STYLE = """
QLineEdit {
    background-color: rgba(255, 255, 255, 14);
    border: 1px solid rgba(255, 255, 255, 30);
    border-radius: 8px;
    color: rgba(255, 255, 255, 220);
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: rgba(100, 160, 255, 190);
    background-color: rgba(255, 255, 255, 20);
}
QLineEdit[placeholderText] {
    color: rgba(255,255,255,55);
}
"""

_ADD_BTN_STYLE = """
QPushButton {
    background-color: rgba(100, 160, 255, 200);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    padding: 0 14px;
}
QPushButton:hover { background-color: rgba(120, 180, 255, 220); }
QPushButton:pressed { background-color: rgba(80, 140, 230, 220); }
"""

_CLOSE_BTN_STYLE = """
QPushButton {
    background: rgba(255,255,255,14);
    color: rgba(255,255,255,160);
    border: none;
    border-radius: 12px;
    font-size: 12px;
}
QPushButton:hover { background: #e05050; color: white; }
"""

_ICON_BTN_STYLE = """
QPushButton {
    background: rgba(255,255,255,14);
    color: rgba(255,255,255,160);
    border: none;
    border-radius: 12px;
    font-size: 12px;
}
QPushButton:hover { background: rgba(255,255,255,35); color: white; }
QPushButton:checked { background: rgba(100,160,255,180); color: white; }
"""

_PIN_BTN_STYLE_OFF = """
QPushButton {
    background: rgba(255,255,255,14);
    color: rgba(255,255,255,80);
    border: none;
    border-radius: 12px;
    font-size: 13px;
}
QPushButton:hover { background: rgba(255,255,255,35); color: rgba(255,255,255,200); }
"""

_PIN_BTN_STYLE_ON = """
QPushButton {
    background: rgba(100,160,255,200);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 13px;
}
QPushButton:hover { background: rgba(120,180,255,220); }
"""

_SCROLL_STYLE = """
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical {
    background: rgba(255,255,255,8);
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,55);
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

_ITEM_STYLE = """
QFrame#item {
    background-color: rgba(255, 255, 255, 8);
    border-radius: 8px;
}
QFrame#item:hover { background-color: rgba(255, 255, 255, 16); }
"""

_CB_STYLE = """
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid rgba(255,255,255,120);
    background: transparent;
}
QCheckBox::indicator:checked {
    background-color: #4caf50;
    border-color: #4caf50;
}
QCheckBox::indicator:unchecked:hover {
    border-color: rgba(100,160,255,200);
}
"""

_DEL_BTN_STYLE = """
QPushButton {
    background: transparent;
    color: rgba(255,255,255,60);
    border: none;
    font-size: 11px;
}
QPushButton:hover { color: #e05050; }
"""

_SUB_CB_STYLE = """
QCheckBox::indicator {
    width: 13px;
    height: 13px;
    border-radius: 3px;
    border: 1.5px solid rgba(255,255,255,80);
    background: transparent;
}
QCheckBox::indicator:checked {
    background-color: rgba(76,175,80,190);
    border-color: rgba(76,175,80,190);
}
QCheckBox::indicator:unchecked:hover {
    border-color: rgba(100,160,255,200);
}
"""

_SUB_INPUT_STYLE = """
QLineEdit {
    background-color: rgba(255, 255, 255, 10);
    border: 1px solid rgba(255, 255, 255, 22);
    border-radius: 6px;
    color: rgba(255, 255, 255, 200);
    padding: 5px 10px;
    font-size: 12px;
}
QLineEdit:focus {
    border-color: rgba(100, 160, 255, 160);
}
"""

_SUB_ADD_BTN_STYLE = """
QPushButton {
    background-color: rgba(100, 160, 255, 170);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover { background-color: rgba(120, 180, 255, 200); }
QPushButton:pressed { background-color: rgba(80, 140, 230, 200); }
"""

_INLINE_EDIT_STYLE = """
QLineEdit {
    background-color: rgba(255, 255, 255, 18);
    border: 1px solid rgba(100, 160, 255, 160);
    border-radius: 4px;
    color: rgba(255, 255, 255, 220);
    padding: 2px 6px;
    font-size: 13px;
}
"""

_SUB_INLINE_EDIT_STYLE = """
QLineEdit {
    background-color: rgba(255, 255, 255, 14);
    border: 1px solid rgba(100, 160, 255, 140);
    border-radius: 3px;
    color: rgba(255, 255, 255, 200);
    padding: 1px 5px;
    font-size: 12px;
}
"""

_HANDLE_STYLE = """
QLabel {
    color: rgba(255,255,255,35);
    font-size: 12px;
}
QLabel:hover {
    color: rgba(255,255,255,100);
}
"""


class _ClickableLabel(QLabel):
    """클릭하면 editing_requested 시그널을 emit하는 라벨."""
    editing_requested = Signal()

    def mouseDoubleClickEvent(self, event):
        self.editing_requested.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.editing_requested.emit()
        super().mousePressEvent(event)


class _SubTaskRow(QWidget):
    def __init__(self, todo: Todo, manager: TodoManager, on_change):
        super().__init__()
        self.todo = todo
        self.manager = manager
        self.on_change = on_change
        self._editing = False
        self._build()

    def _build(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(28, 1, 6, 1)
        row.setSpacing(6)

        self._cb = QCheckBox()
        self._cb.setChecked(self.todo.completed)
        self._cb.setStyleSheet(_SUB_CB_STYLE)
        self._cb.stateChanged.connect(self._toggle)

        self._text_lbl = _ClickableLabel(self.todo.text)
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._text_lbl.editing_requested.connect(self._start_edit)
        if self.todo.completed:
            self._text_lbl.setStyleSheet("color: rgba(255,255,255,55); text-decoration: line-through; font-size: 12px;")
        else:
            self._text_lbl.setStyleSheet("color: rgba(255,255,255,150); font-size: 12px;")

        self._edit_input = QLineEdit(self.todo.text)
        self._edit_input.setStyleSheet(_SUB_INLINE_EDIT_STYLE)
        self._edit_input.hide()
        self._edit_input.returnPressed.connect(self._commit_edit)
        self._edit_input.installEventFilter(self)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(18, 18)
        del_btn.setStyleSheet(_DEL_BTN_STYLE)
        del_btn.clicked.connect(self._delete)

        row.addWidget(self._cb)
        row.addWidget(self._text_lbl, 1)
        row.addWidget(self._edit_input, 1)
        row.addWidget(del_btn)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self._edit_input and event.type() == QEvent.Type.FocusOut:
            self._commit_edit()
        return super().eventFilter(obj, event)

    def _start_edit(self):
        if self.todo.completed:
            return
        self._editing = True
        self._edit_input.setText(self.todo.text)
        self._text_lbl.hide()
        self._edit_input.show()
        self._edit_input.setFocus()
        self._edit_input.selectAll()

    def _commit_edit(self):
        if not self._editing:
            return
        self._editing = False
        text = self._edit_input.text().strip()
        if text and text != self.todo.text:
            self.manager.update_text(self.todo.id, text)
            self.on_change()
        else:
            self._text_lbl.show()
            self._edit_input.hide()

    def _toggle(self):
        self.manager.toggle_complete(self.todo.id)
        self.on_change()

    def _delete(self):
        self.manager.delete(self.todo.id)
        self.on_change()


class _TodoItemWidget(QFrame):
    move_up_requested   = Signal(str)
    move_down_requested = Signal(str)

    def __init__(self, todo: Todo, manager: TodoManager, on_change, sub_tasks: list | None = None,
                 is_first: bool = False, is_last: bool = False):
        super().__init__()
        self.todo = todo
        self.manager = manager
        self.on_change = on_change
        self.sub_tasks = sub_tasks or []
        self._editing = False
        self._is_first = is_first
        self._is_last = is_last
        self.setObjectName("item")
        self.setStyleSheet(_ITEM_STYLE)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 8, 10, 6)
        outer.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(6)

        # ── 드래그 핸들 (위/아래 화살표 버튼) ──────────────────────────────
        handle_col = QVBoxLayout()
        handle_col.setSpacing(0)
        handle_col.setContentsMargins(0, 0, 0, 0)

        up_btn = QPushButton("▲")
        up_btn.setFixedSize(14, 14)
        up_btn.setStyleSheet("""
QPushButton {
    background: transparent;
    color: rgba(255,255,255,40);
    border: none;
    font-size: 8px;
    padding: 0;
}
QPushButton:hover { color: rgba(255,255,255,180); }
QPushButton:disabled { color: rgba(255,255,255,15); }
""")
        up_btn.clicked.connect(lambda: self.move_up_requested.emit(self.todo.id))
        up_btn.setEnabled(not self._is_first and not self.todo.completed)

        down_btn = QPushButton("▼")
        down_btn.setFixedSize(14, 14)
        down_btn.setStyleSheet("""
QPushButton {
    background: transparent;
    color: rgba(255,255,255,40);
    border: none;
    font-size: 8px;
    padding: 0;
}
QPushButton:hover { color: rgba(255,255,255,180); }
QPushButton:disabled { color: rgba(255,255,255,15); }
""")
        down_btn.clicked.connect(lambda: self.move_down_requested.emit(self.todo.id))
        down_btn.setEnabled(not self._is_last and not self.todo.completed)

        handle_col.addWidget(up_btn)
        handle_col.addWidget(down_btn)

        cb = QCheckBox()
        cb.setChecked(self.todo.completed)
        cb.setStyleSheet(_CB_STYLE)
        cb.stateChanged.connect(self._toggle)

        self._text_lbl = _ClickableLabel(self.todo.text)
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._text_lbl.editing_requested.connect(self._start_edit)
        if self.todo.completed:
            self._text_lbl.setStyleSheet("color: rgba(255,255,255,80); text-decoration: line-through; font-size: 13px;")
        else:
            self._text_lbl.setStyleSheet("color: rgba(255,255,255,210); font-size: 13px;")

        self._edit_input = QLineEdit(self.todo.text)
        self._edit_input.setStyleSheet(_INLINE_EDIT_STYLE)
        self._edit_input.hide()
        self._edit_input.returnPressed.connect(self._commit_edit)
        self._edit_input.installEventFilter(self)

        row.addLayout(handle_col)
        row.addWidget(cb)
        row.addWidget(self._text_lbl, 1)
        row.addWidget(self._edit_input, 1)

        # 하위 할 일 개수 뱃지
        if self.sub_tasks:
            done_count = sum(1 for s in self.sub_tasks if s.completed)
            sub_badge = QLabel(f"{done_count}/{len(self.sub_tasks)}")
            sub_badge.setStyleSheet("color: rgba(100,160,255,160); font-size: 10px; padding: 0 2px;")
            row.addWidget(sub_badge)

        add_sub_btn = QPushButton("+")
        add_sub_btn.setFixedSize(22, 22)
        add_sub_btn.setStyleSheet(_ICON_BTN_STYLE)
        add_sub_btn.setToolTip("하위 할 일 추가")
        add_sub_btn.setCheckable(True)
        add_sub_btn.clicked.connect(self._toggle_sub_input)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(22, 22)
        del_btn.setStyleSheet(_DEL_BTN_STYLE)
        del_btn.clicked.connect(self._delete)

        row.addWidget(add_sub_btn)
        row.addWidget(del_btn)

        # ── 타임스탬프 행 ────────────────────────────────────────────────────
        ts_row = QHBoxLayout()
        ts_row.setContentsMargins(30, 0, 0, 0)
        ts_row.setSpacing(0)

        created = QLabel(f"추가: {_fmt(self.todo.created_at)}")
        created.setStyleSheet("color: rgba(255,255,255,70); font-size: 10px;")
        ts_row.addWidget(created)

        if self.todo.completed and self.todo.completed_at:
            sep = QLabel("  •  ")
            sep.setStyleSheet("color: rgba(255,255,255,40); font-size: 10px;")
            done = QLabel(f"완료: {_fmt(self.todo.completed_at)}")
            done.setStyleSheet("color: rgba(100,210,120,160); font-size: 10px;")
            ts_row.addWidget(sep)
            ts_row.addWidget(done)

        ts_row.addStretch()

        outer.addLayout(row)
        outer.addLayout(ts_row)

        # ── 하위 할 일 목록 ───────────────────────────────────────────────────
        if self.sub_tasks:
            sep_line = QFrame()
            sep_line.setFrameShape(QFrame.Shape.HLine)
            sep_line.setMaximumHeight(1)
            sep_line.setStyleSheet("background-color: rgba(255,255,255,10); border: none; margin-left: 24px;")
            outer.addWidget(sep_line)

            for sub in self.sub_tasks:
                outer.addWidget(_SubTaskRow(sub, self.manager, self.on_change))

        # ── 하위 할 일 입력창 ─────────────────────────────────────────────────
        self._sub_inp_container = QWidget()
        sub_inp_row = QHBoxLayout(self._sub_inp_container)
        sub_inp_row.setContentsMargins(28, 4, 6, 2)
        sub_inp_row.setSpacing(6)

        self._sub_input = QLineEdit()
        self._sub_input.setPlaceholderText("하위 할 일 추가…")
        self._sub_input.setStyleSheet(_SUB_INPUT_STYLE)
        self._sub_input.setFixedHeight(28)
        self._sub_input.returnPressed.connect(self._add_sub)

        sub_add_btn = QPushButton("+")
        sub_add_btn.setFixedSize(28, 28)
        sub_add_btn.setStyleSheet(_SUB_ADD_BTN_STYLE)
        sub_add_btn.clicked.connect(self._add_sub)

        sub_inp_row.addWidget(self._sub_input, 1)
        sub_inp_row.addWidget(sub_add_btn)
        self._sub_inp_container.hide()
        outer.addWidget(self._sub_inp_container)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self._edit_input and event.type() == QEvent.Type.FocusOut:
            self._commit_edit()
        return super().eventFilter(obj, event)

    def _start_edit(self):
        if self.todo.completed:
            return
        self._editing = True
        self._edit_input.setText(self.todo.text)
        self._text_lbl.hide()
        self._edit_input.show()
        self._edit_input.setFocus()
        self._edit_input.selectAll()

    def _commit_edit(self):
        if not self._editing:
            return
        self._editing = False
        text = self._edit_input.text().strip()
        if text and text != self.todo.text:
            self.manager.update_text(self.todo.id, text)
            self.on_change()
        else:
            self._text_lbl.show()
            self._edit_input.hide()

    def _toggle_sub_input(self, checked: bool):
        if checked:
            self._sub_inp_container.show()
            self._sub_input.setFocus()
        else:
            self._sub_inp_container.hide()

    def _add_sub(self):
        text = self._sub_input.text().strip()
        if text:
            self.manager.add(text, parent_id=self.todo.id)
            self._sub_input.clear()
            self._sub_inp_container.hide()
            self.on_change()

    def _toggle(self):
        self.manager.toggle_complete(self.todo.id)
        self.on_change()

    def _delete(self):
        self.manager.delete(self.todo.id)
        self.on_change()


_SYNC_COLORS = {
    SyncState.SYNCED:     ("●", "rgba(100,210,120,220)"),
    SyncState.SYNCING:    ("●", "rgba(100,160,255,220)"),
    SyncState.PENDING:    ("●", "rgba(255,200,60,220)"),
    SyncState.OFFLINE:    ("●", "rgba(160,160,160,200)"),
    SyncState.AUTH_ERROR: ("●", "rgba(220,80,80,220)"),
}


class OverlayWindow(QWidget):
    todos_changed = Signal()

    def __init__(self, manager: TodoManager, settings: SettingsManager, checker):
        super().__init__()
        self.manager = manager
        self.settings = settings
        self._log_mode = False
        self._pinned = False
        self._anim: QPropertyAnimation | None = None
        self._refresh_fingerprint: tuple = ()
        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(400)
        self._leave_timer.timeout.connect(self._animated_hide)
        # 오버레이가 표시될 디스플레이 원점 (다중 디스플레이)
        self._origin_x = 12
        self._origin_y = 12
        self._setup_window()
        self._build_ui()
        self._settings_dialog = SettingsDialog(self.settings, checker)
        self._settings_dialog.set_todo_manager(self.manager)
        self._settings_dialog.set_overlay_callbacks(
            on_width=self._apply_width,
            on_delay=lambda v: self._leave_timer.setInterval(v),
        )

    def _setup_window(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        if platform.system() != "Darwin":
            flags |= Qt.WindowType.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(380)
        self.move(12, 12)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._container = QFrame()
        self._container.setObjectName("container")
        self._container.setStyleSheet(_CONTAINER_STYLE)
        root.addWidget(self._container)

        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("📝  Working Memo")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: rgba(255,255,255,100); font-size: 11px;")

        self._sync_dot = QLabel("●")
        self._sync_dot.setToolTip("오프라인")
        self._sync_dot.setStyleSheet("color: rgba(160,160,160,200); font-size: 10px;")

        self._log_btn = QPushButton("📋")
        self._log_btn.setFixedSize(24, 24)
        self._log_btn.setStyleSheet(_ICON_BTN_STYLE)
        self._log_btn.setCheckable(True)
        self._log_btn.setToolTip("완료 로그")
        self._log_btn.clicked.connect(self._toggle_log)

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(24, 24)
        self._settings_btn.setStyleSheet(_ICON_BTN_STYLE)
        self._settings_btn.setToolTip("설정")
        self._settings_btn.clicked.connect(self._open_settings)

        # 핀(고정) 버튼
        self._pin_btn = QPushButton("📌")
        self._pin_btn.setFixedSize(24, 24)
        self._pin_btn.setStyleSheet(_PIN_BTN_STYLE_OFF)
        self._pin_btn.setToolTip("창 고정 (마우스가 떠나도 닫히지 않음)")
        self._pin_btn.setCheckable(True)
        self._pin_btn.clicked.connect(self._toggle_pin)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(_CLOSE_BTN_STYLE)
        close_btn.clicked.connect(self._animated_hide)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self._sync_dot)
        hdr.addSpacing(6)
        hdr.addWidget(self._count_lbl)
        hdr.addSpacing(8)
        hdr.addWidget(self._log_btn)
        hdr.addSpacing(4)
        hdr.addWidget(self._settings_btn)
        hdr.addSpacing(4)
        hdr.addWidget(self._pin_btn)
        hdr.addSpacing(4)
        hdr.addWidget(close_btn)

        # ── Input row ────────────────────────────────────────────────────────
        self._inp_container = QWidget()
        inp_row = QHBoxLayout(self._inp_container)
        inp_row.setContentsMargins(0, 0, 0, 0)
        inp_row.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("새 할 일 입력 후 Enter…")
        self._input.setStyleSheet(_INPUT_STYLE)
        self._input.setFixedHeight(36)
        self._input.returnPressed.connect(self._add)

        add_btn = QPushButton("추가")
        add_btn.setFixedHeight(36)
        add_btn.setMinimumWidth(52)
        add_btn.setStyleSheet(_ADD_BTN_STYLE)
        add_btn.clicked.connect(self._add)

        inp_row.addWidget(self._input, 1)
        inp_row.addWidget(add_btn)

        # ── Divider ──────────────────────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setMaximumHeight(1)
        div.setStyleSheet("background-color: rgba(255,255,255,18); border: none;")

        # ── Scroll area ──────────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(_SCROLL_STYLE)
        self._scroll.setMinimumHeight(120)
        self._scroll.setMaximumHeight(460)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)

        self._empty_lbl = QLabel("할 일이 없습니다 🎉")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet("color: rgba(255,255,255,50); font-size: 13px; padding: 24px 0;")

        layout.addLayout(hdr)
        layout.addWidget(self._inp_container)
        layout.addWidget(div)
        layout.addWidget(self._empty_lbl)
        layout.addWidget(self._scroll)

        self._sync_manager = None
        self._refresh()

    def _toggle_pin(self, checked: bool):
        self._pinned = checked
        self._pin_btn.setStyleSheet(_PIN_BTN_STYLE_ON if checked else _PIN_BTN_STYLE_OFF)
        if checked:
            self._leave_timer.stop()

    def _add(self):
        text = self._input.text().strip()
        if text:
            self.manager.add(text)
            self._input.clear()
            self._refresh()
            if self._sync_manager:
                self._sync_manager.push_now()

    def _refresh(self):
        todos = self.manager.get_all()

        sub_map: dict[str, list] = {}
        top_incomplete: list = []
        top_complete:   list = []
        for t in todos:
            if t.parent_id:
                sub_map.setdefault(t.parent_id, []).append(t)
            elif t.completed:
                top_complete.append(t)
            else:
                top_incomplete.append(t)

        for lst in sub_map.values():
            lst.sort(key=lambda t: (t.completed, t.created_at or ""))

        # 미완료는 order 순, 완료는 completed_at 역순
        top_incomplete.sort(key=lambda t: t.order)
        top_complete.sort(key=lambda t: t.completed_at or "", reverse=True)

        display    = top_complete if self._log_mode else (top_incomplete + top_complete)
        empty_text = "완료된 항목이 없습니다" if self._log_mode else "할 일이 없습니다 🎉"

        fingerprint = tuple(
            (t.id, t.completed, t.text, t.order,
             tuple((s.id, s.completed, s.text) for s in sub_map.get(t.id, [])))
            for t in display
        )
        if fingerprint != self._refresh_fingerprint:
            self._refresh_fingerprint = fingerprint
            while self._list_layout.count() > 1:
                item = self._list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self._empty_lbl.setText(empty_text)
            if not display:
                self._empty_lbl.show()
                self._scroll.hide()
            else:
                self._empty_lbl.hide()
                self._scroll.show()
                incomplete_ids = {t.id for t in top_incomplete}
                for i, todo in enumerate(display):
                    subs = sub_map.get(todo.id, [])
                    is_incomplete = todo.id in incomplete_ids
                    is_first = is_incomplete and i == 0
                    is_last  = is_incomplete and (i == len(top_incomplete) - 1)
                    w = _TodoItemWidget(
                        todo, self.manager, self._on_todo_changed, subs,
                        is_first=is_first, is_last=is_last,
                    )
                    w.move_up_requested.connect(self._move_up)
                    w.move_down_requested.connect(self._move_down)
                    self._list_layout.insertWidget(self._list_layout.count() - 1, w)
            self.adjustSize()

        done  = len(top_complete)
        total = len(top_incomplete) + len(top_complete)
        self._count_lbl.setText(f"{done}/{total}" if total else "")

    def _move_up(self, todo_id: str):
        self.manager.move_up(todo_id)
        self._refresh_fingerprint = ()
        self._refresh()
        if self._sync_manager:
            self._sync_manager.push_now()

    def _move_down(self, todo_id: str):
        self.manager.move_down(todo_id)
        self._refresh_fingerprint = ()
        self._refresh()
        if self._sync_manager:
            self._sync_manager.push_now()

    def _on_todo_changed(self):
        self._refresh_fingerprint = ()
        self._refresh()
        if self._sync_manager:
            self._sync_manager.push_now()

    def _toggle_log(self):
        self._log_mode = self._log_btn.isChecked()
        self._inp_container.setVisible(not self._log_mode)
        self._refresh()

    def set_sync_manager(self, sync_manager):
        self._sync_manager = sync_manager
        sync_manager.status_changed.connect(self._on_sync_status)
        sync_manager.todos_refreshed.connect(self._refresh)
        self._on_sync_status(sync_manager.state)

    def _on_sync_status(self, state: str):
        dot, color = _SYNC_COLORS.get(state, ("●", "rgba(160,160,160,200)"))
        tooltips = {
            SyncState.SYNCED:     "동기화됨",
            SyncState.SYNCING:    "동기화 중...",
            SyncState.PENDING:    "미동기화 항목 있음",
            SyncState.OFFLINE:    "오프라인",
            SyncState.AUTH_ERROR: "인증 오류",
        }
        self._sync_dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self._sync_dot.setToolTip(tooltips.get(state, state))

    def _apply_width(self, v: int):
        self.setFixedWidth(v)

    def _open_settings(self):
        self._settings_dialog.show_centered()
        self._leave_timer.stop()

    # ── 애니메이션 ──────────────────────────────────────────────────────────

    def _stop_anim(self):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()

    def set_display_origin(self, x: int, y: int):
        """어느 디스플레이 코너에서 트리거됐는지 기록."""
        self._origin_x = x + 12
        self._origin_y = y + 12

    def _animated_show(self):
        self._stop_anim()
        self._refresh()
        super().show()
        self.activateWindow()
        self.raise_()
        self._input.setFocus()

        ox, oy = self._origin_x, self._origin_y

        if not self.settings.animation:
            self.move(ox, oy)
            return

        h = self.sizeHint().height() or self.height() or 300
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(self.settings.anim_duration)
        self._anim.setStartValue(QPoint(ox, oy - h))
        self._anim.setEndValue(QPoint(ox, oy))
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _animated_hide(self):
        self._stop_anim()
        if not self.isVisible():
            return
        if self._pinned:
            return

        if not self.settings.animation:
            super().hide()
            return

        self._leave_timer.stop()
        dur = max(60, self.settings.anim_duration - 40)
        h   = self.height() or 300
        cur = self.pos()
        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(dur)
        self._anim.setStartValue(cur)
        self._anim.setEndValue(QPoint(cur.x(), cur.y() - h))
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(super().hide)
        self._anim.start()

    # ── toggle / events ─────────────────────────────────────────────────────

    def toggle(self):
        if self.isVisible():
            self._animated_hide()
        else:
            self._animated_show()

    def enterEvent(self, event):
        self._leave_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._pinned:
            super().leaveEvent(event)
            return
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self._leave_timer.start()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._animated_hide()
        super().keyPressEvent(event)
