from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
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


class _RangePage(QWidget):
    """범위설정 탭"""
    corner_size_changed = Signal(int)

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        lay.addWidget(_section("마우스 인식 범위"))
        lay.addWidget(_divider())

        row = QHBoxLayout()
        row.addWidget(_label("코너 감지 범위"))
        row.addStretch()
        self._val = QLabel(f"{settings.corner_size} px")
        self._val.setStyleSheet(_VALUE_LABEL)
        row.addWidget(self._val)
        lay.addLayout(row)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(5, 100)
        self._slider.setValue(settings.corner_size)
        self._slider.setStyleSheet(_SLIDER_STYLE)
        self._slider.valueChanged.connect(self._on_change)
        lay.addWidget(self._slider)

        lay.addWidget(_hint("화면 좌측 상단 코너에서 감지할 픽셀 범위입니다. 값이 클수록 더 넓은 영역에서 트리거됩니다. (5 – 100 px)"))
        lay.addStretch()

    def _on_change(self, v: int):
        self._val.setText(f"{v} px")
        self.settings.corner_size = v
        self.corner_size_changed.emit(v)


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


class _UIPage(QWidget):
    """UI 설정 탭"""
    def __init__(self, settings: SettingsManager):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

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

        self._settings = settings
        self.overlay_width_changed = None
        self.leave_delay_changed = None

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
    corner_size_changed = Signal(int)

    _TABS = [
        ("🔐", "접속정보"),
        ("🎯", "범위설정"),
        ("📋", "기록 관리"),
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

        # Header
        hdr = QHBoxLayout()
        title = QLabel("⚙  설정")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(_CLOSE_BTN_STYLE)
        close_btn.clicked.connect(self.hide)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        outer.addLayout(hdr)

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
        self._page_ui = _UIPage(settings=self.settings)
        self._page_update = _UpdatePage(checker=self._checker)

        self._page_range.corner_size_changed.connect(self.corner_size_changed)

        self._stack.addWidget(self._page_access)
        self._stack.addWidget(self._page_range)
        self._stack.addWidget(self._page_history)
        self._stack.addWidget(self._page_ui)
        self._stack.addWidget(self._page_update)

        body.addWidget(self._stack, 1)
        outer.addLayout(body)

        self._switch(0)

    def _switch(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.setStyleSheet(_TAB_ACTIVE if i == idx else _TAB_DEFAULT)

    def set_todo_manager(self, manager):
        self._page_history.set_todo_manager(manager)

    def set_sync_manager(self, sync_manager):
        self._page_history.set_sync_manager(sync_manager)

    def set_overlay_callbacks(self, on_width, on_delay):
        self._page_ui.overlay_width_changed = on_width
        self._page_ui.leave_delay_changed = on_delay

    def show_centered(self):
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
