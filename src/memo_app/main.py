import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .db import DatabaseManager
from .monitor import CornerMonitor, DisplayCorner, get_physical_monitor_rects
from .overlay import OverlayWindow
from .settings_manager import SettingsManager
from .sync_manager import SyncManager
from .todo_manager import TodoManager
from .updater import UpdateChecker

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

    server = QLocalServer(app)
    QLocalServer.removeServer(_INSTANCE_KEY)
    server.listen(_INSTANCE_KEY)

    settings = SettingsManager()
    manager  = TodoManager()
    db       = DatabaseManager()
    checker  = UpdateChecker()
    overlay  = OverlayWindow(manager, settings, checker)

    def _on_new_connection():
        conn = server.nextPendingConnection()
        if conn:
            conn.waitForReadyRead(200)
            conn.disconnectFromServer()
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

    toggle_act  = menu.addAction("📝   열기 / 닫기")
    toggle_act.triggered.connect(overlay.toggle)
    menu.addSeparator()

    # 업데이트 메뉴 아이템 (평소엔 숨김, 업데이트 발견 시 표시)
    _update_act = menu.addAction("🔄   업데이트 확인 중...")
    _update_act.setEnabled(False)
    _update_act.setVisible(False)

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

    # ── 업데이트 체크 연동 ────────────────────────────────────────────────────
    def _on_update_available(version: str, url: str):
        _update_act.setText(f"🔄   v{version}으로 업데이트 가능")
        _update_act.setEnabled(True)
        _update_act.setVisible(True)
        _update_act.triggered.connect(
            lambda: _open_update_tab()
        )
        tray.showMessage(
            "Working Memo 업데이트",
            f"새 버전 v{version}이 출시됐습니다. 설정 → 업데이트 탭에서 설치하세요.",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )

    def _open_update_tab():
        overlay._settings_dialog._switch(5)  # 업데이트 탭 인덱스 (로그 탭 추가로 +1)
        overlay._settings_dialog.show_centered()

    checker.update_available.connect(_on_update_available)

    # ── Corner + Ctrl monitor ─────────────────────────────────────────────────
    def _build_corners() -> list[DisplayCorner]:
        phys_rects = get_physical_monitor_rects()
        configs = list(settings.display_configs)
        while len(configs) < len(phys_rects):
            configs.append({"corner_size": settings.corner_size, "enabled": True})
        return [
            DisplayCorner(
                origin_x=left,
                origin_y=top,
                corner_size=cfg.get("corner_size", settings.corner_size),
                enabled=cfg.get("enabled", True),
                name=f"디스플레이 {i + 1}",
            )
            for i, ((left, top, _r, _b), cfg) in enumerate(zip(phys_rects, configs))
        ]

    monitor = CornerMonitor(
        corners=_build_corners(),
        quick_key=settings.quick_key,
        trigger_mode=settings.trigger_mode,
    )
    def _on_corner_triggered(origin_x: int, origin_y: int):
        overlay.set_display_origin(origin_x, origin_y)
        overlay.toggle()

    monitor.corner_triggered.connect(_on_corner_triggered)
    monitor.start()

    def _on_displays_changed():
        monitor.corners = _build_corners()

    def _on_trigger_changed(mode: str, key: str):
        monitor.stop_listeners()
        monitor.wait()
        monitor.trigger_mode = mode
        monitor.quick_key    = key
        monitor.start()

    overlay._settings_dialog.displays_changed.connect(_on_displays_changed)
    overlay._settings_dialog.trigger_changed.connect(_on_trigger_changed)

    def _cleanup():
        monitor.stop_listeners()
        db.disconnect()
        QLocalServer.removeServer(_INSTANCE_KEY)

    app.aboutToQuit.connect(_cleanup)

    # ── 초기 표시 ────────────────────────────────────────────────────────────
    overlay.toggle()
    QTimer.singleShot(500, sync.start)
    # 시작 10초 후 업데이트 자동 체크
    QTimer.singleShot(10_000, checker.check_async)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
