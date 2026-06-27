import os
import platform
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _apply_macos_policy() -> None:
    """macOS: 독(Dock) 아이콘을 숨기고 메뉴바 전용 앱으로 설정."""
    if platform.system() != "Darwin":
        return
    try:
        import AppKit  # pyobjc-framework-Cocoa
        app = AppKit.NSApplication.sharedApplication()
        # Accessory: Dock·App Switcher에서 숨김, 메뉴바 상태 아이콘만 표시
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    except Exception:
        pass

from .db import DatabaseManager
from .monitor import CornerMonitor, DisplayCorner, get_physical_monitor_rects
from .overlay import OverlayWindow
from .settings_manager import SettingsManager
from .sync_manager import SyncManager
from .todo_manager import TodoManager
from .updater import UpdateChecker

_INSTANCE_KEY = "WorkingMemo-SingleInstance"

# ── 로그인 자동 시작 (LaunchAgent) ───────────────────────────────────────────

_AGENT_LABEL = "com.workingmemo.app"
_AGENT_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{_AGENT_LABEL}.plist"


def _autostart_args() -> list[str] | None:
    """LaunchAgent에 등록할 실행 인자. 번들이면 [exe], 소스이면 [python, run.py]."""
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).resolve())]
    run_py = Path(__file__).resolve().parents[2] / "run.py"
    if run_py.exists():
        return [str(Path(sys.executable).resolve()), str(run_py)]
    return None


def _is_autostart() -> bool:
    return _AGENT_PLIST.exists()


def _set_autostart(enabled: bool, args: list[str]) -> None:
    uid = os.getuid()
    if enabled:
        items = "\n".join(f"        <string>{a}</string>" for a in args)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_AGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
{items}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
        _AGENT_PLIST.parent.mkdir(parents=True, exist_ok=True)
        _AGENT_PLIST.write_text(plist, encoding="utf-8")
        subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", str(_AGENT_PLIST)],
            capture_output=True,
        )
    else:
        if _AGENT_PLIST.exists():
            subprocess.run(
                ["launchctl", "bootout", f"gui/{uid}", str(_AGENT_PLIST)],
                capture_output=True,
            )
            _AGENT_PLIST.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────


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
    _apply_macos_policy()

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
    tray.setToolTip("Working Memo  |  트리거 키 + 코너(또는 키만)로 열기/닫기")

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
        QMenu::item:disabled { color: rgba(255,255,255,80); }
        QMenu::separator { height: 1px; background: rgba(255,255,255,20); margin: 4px 8px; }
    """)

    toggle_act = menu.addAction("📝   열기 / 닫기")
    toggle_act.triggered.connect(overlay.toggle)
    menu.addSeparator()

    # ── 로그인 시 자동 시작 토글 ──────────────────────────────────────────────
    autostart_act = menu.addAction("🚀   로그인 시 자동 시작")
    autostart_act.setCheckable(True)
    _args = _autostart_args()
    if _args:
        autostart_act.setChecked(_is_autostart())

        def _toggle_autostart(checked: bool):
            _set_autostart(checked, _args)

        autostart_act.triggered.connect(_toggle_autostart)
    else:
        autostart_act.setEnabled(False)

    menu.addSeparator()

    # 업데이트 메뉴 아이템 (평소엔 숨김, 업데이트 발견 시 표시)
    _update_act = menu.addAction("🔄   업데이트 확인 중...")
    _update_act.setEnabled(False)
    _update_act.setVisible(False)

    menu.addSeparator()

    # 권한 문제 감지 시 표시 (평소엔 숨김)
    _perm_act = menu.addAction("⚠️   입력 모니터링 권한 필요")
    _perm_act.setVisible(False)
    def _open_privacy_settings():
        subprocess.Popen(["open",
            "x-apple.systempreferences:com.apple.preference.security"
            "?Privacy_Accessibility"])
    _perm_act.triggered.connect(_open_privacy_settings)

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
        _update_act.triggered.connect(lambda: _open_update_tab())
        tray.showMessage(
            "Working Memo 업데이트",
            f"새 버전 v{version}이 출시됐습니다. 설정 → 업데이트 탭에서 설치하세요.",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )

    def _open_update_tab():
        overlay._settings_dialog._switch(5)
        overlay._settings_dialog.show_centered()

    checker.update_available.connect(_on_update_available)

    # ── Corner + key monitor ──────────────────────────────────────────────────
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
        display_rects=get_physical_monitor_rects(),
    )

    def _on_corner_triggered(origin_x: int, origin_y: int):
        overlay.set_display_origin(origin_x, origin_y)
        overlay.toggle()

    monitor.corner_triggered.connect(_on_corner_triggered)
    monitor.start()

    def _on_displays_changed():
        monitor.corners = _build_corners()
        monitor.display_rects = get_physical_monitor_rects()

    def _on_trigger_changed(mode: str, key: str):
        monitor.trigger_mode = mode
        monitor.quick_key    = key

        if not monitor.isRunning():
            monitor.start()
            return

        def _do_restart():
            try:
                monitor.finished.disconnect(_do_restart)
            except RuntimeError:
                pass
            monitor.events_received = 0  # 재시작 시 카운터 리셋
            monitor.start()

        # QueuedConnection: finished는 QThread 스레드에서 emit되므로
        # DirectConnection이면 _do_restart가 QThread 스레드에서 실행된다.
        # QueuedConnection으로 메인 스레드에서 실행되도록 보장.
        monitor.finished.connect(_do_restart, Qt.ConnectionType.QueuedConnection)
        monitor.stop_listeners()

    overlay._settings_dialog.displays_changed.connect(_on_displays_changed)
    overlay._settings_dialog.trigger_changed.connect(_on_trigger_changed)

    def _check_input_permission():
        """앱 시작 후 입력 이벤트가 하나도 안 왔으면 권한 문제로 판단."""
        if monitor.events_received == 0:
            _perm_act.setVisible(True)
            tray.showMessage(
                "WorkingMemo — 권한 필요",
                "키보드/마우스 모니터링 권한이 없습니다.\n"
                "시스템 설정 → 개인 정보 보호 및 보안\n"
                "→ 손쉬운 사용(Accessibility) 및 입력 모니터링에서\n"
                "WorkingMemo를 허용한 후 앱을 재시작해주세요.",
                QSystemTrayIcon.MessageIcon.Warning,
                10000,
            )

    # 8초 후 권한 체크 (앱 시작 직후엔 마우스/키 이벤트가 없을 수 있어서)
    QTimer.singleShot(8000, _check_input_permission)

    def _cleanup():
        monitor.stop_listeners()
        db.disconnect()
        QLocalServer.removeServer(_INSTANCE_KEY)

    app.aboutToQuit.connect(_cleanup)

    # ── 초기 표시 ────────────────────────────────────────────────────────────
    overlay.toggle()
    QTimer.singleShot(500, sync.start)
    QTimer.singleShot(10_000, checker.check_async)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
