import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .db import DatabaseManager
from .monitor import CornerMonitor
from .overlay import OverlayWindow
from .settings_manager import SettingsManager
from .sync_manager import SyncManager
from .todo_manager import TodoManager

_INSTANCE_KEY = "WorkingMemo-SingleInstance"


def _make_tray_icon() -> QIcon:
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(60, 100, 200))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(2, 2, 28, 28, 7, 7)
    p.setPen(QColor("white"))
    font = p.font()
    font.setPixelSize(17)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "✎")
    p.end()
    return QIcon(px)


def _already_running() -> bool:
    """이미 실행 중인 인스턴스가 있으면 True. 있으면 그쪽에 'show' 신호도 보낸다."""
    sock = QLocalSocket()
    sock.connectToServer(_INSTANCE_KEY)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.disconnectFromServer()
        return True
    return False


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("WorkingMemo")

    # ── 단일 인스턴스 보호 ────────────────────────────────────────────────────
    if _already_running():
        print("[WorkingMemo] 이미 실행 중입니다.")
        sys.exit(0)

    # 이 프로세스가 서버 역할
    server = QLocalServer(app)
    QLocalServer.removeServer(_INSTANCE_KEY)   # 이전에 죽은 소켓 정리
    server.listen(_INSTANCE_KEY)

    settings = SettingsManager()
    manager  = TodoManager()
    db       = DatabaseManager()
    overlay  = OverlayWindow(manager, settings)

    def _on_new_connection():
        conn = server.nextPendingConnection()
        if conn:
            conn.waitForReadyRead(200)
            conn.disconnectFromServer()
        # 다른 인스턴스가 show 요청 → 오버레이 표시
        if not overlay.isVisible():
            overlay.toggle()

    server.newConnection.connect(_on_new_connection)

    # ── SyncManager ───────────────────────────────────────────────────────────
    sync = SyncManager(db, settings, manager)
    overlay.set_sync_manager(sync)
    overlay._settings_dialog.set_sync_manager(sync)

    # ── System tray ───────────────────────────────────────────────────────────
    tray = QSystemTrayIcon(_make_tray_icon(), app)
    tray.setToolTip("Working Memo  |  Ctrl + 좌측 상단 코너로 열기/닫기")

    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            background-color: #0e0e18;
            color: rgba(255,255,255,210);
            border: 1px solid rgba(255,255,255,28);
            border-radius: 8px;
            padding: 4px;
        }
        QMenu::item { padding: 7px 20px; border-radius: 5px; }
        QMenu::item:selected { background: rgba(100,160,255,160); }
        QMenu::separator { height: 1px; background: rgba(255,255,255,20); margin: 4px 8px; }
    """)

    toggle_act = menu.addAction("📝   열기 / 닫기")
    toggle_act.triggered.connect(overlay.toggle)
    menu.addSeparator()
    quit_act = menu.addAction("✕   종료")
    quit_act.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: overlay.toggle()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()

    # ── Corner + Ctrl monitor ─────────────────────────────────────────────────
    monitor = CornerMonitor(corner_size=settings.corner_size)
    monitor.corner_triggered.connect(overlay.toggle)
    monitor.start()

    overlay._settings_dialog.corner_size_changed.connect(
        lambda v: setattr(monitor, "corner_size", v)
    )

    def _cleanup():
        monitor.stop_listeners()
        db.disconnect()
        QLocalServer.removeServer(_INSTANCE_KEY)

    app.aboutToQuit.connect(_cleanup)

    # ── 초기 표시 ────────────────────────────────────────────────────────────
    overlay.toggle()
    # sync는 약간 늦게 시작해 UI 렌더링 먼저 완료
    QTimer.singleShot(500, sync.start)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
