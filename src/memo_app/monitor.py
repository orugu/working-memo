from __future__ import annotations

import platform
import queue
from dataclasses import dataclass

from PySide6.QtCore import QThread, QTimer, Signal
from pynput import keyboard, mouse

_IS_MAC = platform.system() == "Darwin"

# macOS Quartz: key_only 모드에서 트리거 키가 다른 앱에 전달되지 않도록 억제
_HAS_QUARTZ = False
if _IS_MAC:
    try:
        import Quartz as _Quartz
        _HAS_QUARTZ = True
    except ImportError:
        pass

# macOS 가상 키코드 (Quartz 억제용)
_DARWIN_KEY_CODES: dict[str, set[int]] = {
    "ctrl":  {59, 62}, "alt":  {58, 61},
    "shift": {56, 60}, "cmd":  {55, 54},
    "f1": {122}, "f2": {120}, "f3": {99},  "f4": {118},
    "f5": {96},  "f6": {97},  "f7": {98},  "f8": {100},
    "f9": {101}, "f10": {109}, "f11": {103}, "f12": {111},
}

_cmd_keys: set = set()
for _k in ("cmd", "cmd_l", "cmd_r"):
    if hasattr(keyboard.Key, _k):
        _cmd_keys.add(getattr(keyboard.Key, _k))

_MOD_KEYS: dict[str, frozenset] = {
    "ctrl":  frozenset({keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl}),
    "alt":   frozenset({keyboard.Key.alt_l,  keyboard.Key.alt_r,  keyboard.Key.alt}),
    "shift": frozenset({keyboard.Key.shift_l, keyboard.Key.shift_r, keyboard.Key.shift}),
    "cmd":   frozenset(_cmd_keys),
}


@dataclass
class DisplayCorner:
    """한 디스플레이의 좌측 상단 코너 감지 영역 (물리 픽셀 기준)."""
    origin_x: int
    origin_y: int
    corner_size: int = 20
    enabled: bool = True
    name: str = ""

    def in_corner(self, x: int, y: int) -> bool:
        return (
            self.enabled
            and abs(x - self.origin_x) <= self.corner_size
            and abs(y - self.origin_y) <= self.corner_size
        )


def get_physical_monitor_rects() -> list[tuple[int, int, int, int]]:
    """물리 픽셀 기준 모니터 좌표 (left, top, right, bottom) 목록을 반환한다."""
    if platform.system() == "Windows":
        import ctypes
        from ctypes import wintypes
        rects: list[tuple[int, int, int, int]] = []
        _Proc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_long,
        )
        def _cb(hmon, hdc, lprect, _):
            r = lprect.contents
            rects.append((r.left, r.top, r.right, r.bottom))
            return True
        ctypes.windll.user32.EnumDisplayMonitors(None, None, _Proc(_cb), 0)
        return rects or [(0, 0, 1920, 1080)]
    else:
        from PySide6.QtGui import QGuiApplication
        app = QGuiApplication.instance()
        if app is None:
            return [(0, 0, 1920, 1080)]
        rects = []
        for screen in app.screens():
            geom = screen.geometry()
            rects.append((geom.left(), geom.top(), geom.right() + 1, geom.bottom() + 1))
        return rects or [(0, 0, 1920, 1080)]


class CornerMonitor(QThread):
    """
    트리거 방식:
      corner_key — 마우스가 코너에 있을 때 퀵키 입력
      key_only   — 마우스 위치 무관, 퀵키만 입력

    pynput 콜백은 네이티브 스레드에서 실행되므로 Qt 시그널을 직접 emit하면
    크로스-스레드 문제가 발생한다. 대신 SimpleQueue에 넣고, 메인 스레드
    QTimer가 주기적으로 드레인하여 안전하게 시그널을 emit한다.
    """

    corner_triggered = Signal(int, int)  # (origin_x, origin_y)

    def __init__(
        self,
        corners: list[DisplayCorner] | None = None,
        quick_key: str = "ctrl",
        trigger_mode: str = "corner_key",
        display_rects: list[tuple[int, int, int, int]] | None = None,
    ):
        super().__init__()
        self.corners: list[DisplayCorner] = corners if corners is not None else [DisplayCorner(0, 0, 20)]
        self.quick_key    = quick_key
        self.trigger_mode = trigger_mode
        self.display_rects: list[tuple[int, int, int, int]] = display_rects or []
        self._key_pressed   = False
        self._was_in_corner = False
        self._mouse_x = 0
        self._mouse_y = 0
        self._mouse_listener: mouse.Listener | None = None
        self._key_listener:   keyboard.Listener | None = None
        self.events_received: int = 0  # pynput 권한 체크용 카운터

        # pynput → 메인 스레드 안전 전달 채널
        self._trigger_queue: queue.SimpleQueue = queue.SimpleQueue()
        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(25)  # 25ms ≈ 40fps
        self._drain_timer.timeout.connect(self._drain_triggers)

    # ── 메인 스레드에서 트리거 큐 드레인 ────────────────────────────────────

    def _drain_triggers(self) -> None:
        while not self._trigger_queue.empty():
            try:
                ox, oy = self._trigger_queue.get_nowait()
                self.corner_triggered.emit(ox, oy)
            except Exception:
                break

    # ── QThread 시작/정지 ────────────────────────────────────────────────────

    def start(self, priority: QThread.Priority = QThread.Priority.InheritPriority) -> None:
        self._drain_timer.start()
        super().start(priority)

    def stop_listeners(self) -> None:
        self._drain_timer.stop()
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
        if self._key_listener:
            try:
                self._key_listener.stop()
            except Exception:
                pass

    # ── 헬퍼 ─────────────────────────────────────────────────────────────────

    @property
    def corner_size(self) -> int:
        return self.corners[0].corner_size if self.corners else 20

    @corner_size.setter
    def corner_size(self, v: int):
        for c in self.corners:
            c.corner_size = v

    def _in_any_corner(self, x: int, y: int) -> bool:
        return any(c.in_corner(x, y) for c in self.corners)

    def _corner_origin(self, x: int, y: int) -> tuple[int, int]:
        for c in self.corners:
            if c.in_corner(x, y):
                return c.origin_x, c.origin_y
        return 0, 0

    def _display_origin_for_pos(self, x: int, y: int) -> tuple[int, int]:
        """마우스 위치가 속한 디스플레이의 좌상단 origin (thread-safe: Qt 호출 없음)."""
        for left, top, right, bottom in self.display_rects:
            if left <= x < right and top <= y < bottom:
                return left, top
        if self.corners:
            nearest = min(self.corners, key=lambda c: abs(c.origin_x - x) + abs(c.origin_y - y))
            return nearest.origin_x, nearest.origin_y
        return 0, 0

    def _matches(self, key) -> bool:
        name = self.quick_key
        if name in _MOD_KEYS:
            return key in _MOD_KEYS[name]
        if name.startswith("f") and name[1:].isdigit():
            fkey = getattr(keyboard.Key, name, None)
            return fkey is not None and key == fkey
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower() == name
        return False

    # ── 리스너 스레드 ─────────────────────────────────────────────────────────

    def run(self) -> None:
        self._key_pressed   = False
        self._was_in_corner = False

        # pynput 콜백에서 직접 queue에 넣기만 함 — Qt/GUI 호출 없음
        def _enqueue(ox: int, oy: int) -> None:
            self._trigger_queue.put((ox, oy))

        def on_move(x: int, y: int) -> None:
            self.events_received += 1
            self._mouse_x = x
            self._mouse_y = y
            if self.trigger_mode == "corner_key":
                in_corner = self._in_any_corner(x, y)
                if self._key_pressed and in_corner and not self._was_in_corner:
                    ox, oy = self._display_origin_for_pos(x, y)
                    _enqueue(ox, oy)
                self._was_in_corner = in_corner

        def on_press(key) -> None:
            self.events_received += 1
            if not self._matches(key):
                return
            if self._key_pressed:  # key repeat 무시
                return
            self._key_pressed = True
            if self.trigger_mode == "key_only":
                ox, oy = self._display_origin_for_pos(self._mouse_x, self._mouse_y)
                _enqueue(ox, oy)
            elif self._in_any_corner(self._mouse_x, self._mouse_y):
                ox, oy = self._corner_origin(self._mouse_x, self._mouse_y)
                _enqueue(ox, oy)
                self._was_in_corner = True  # on_move 중복 트리거 방지

        def on_release(key) -> None:
            self.events_received += 1
            if self._matches(key):
                self._key_pressed   = False
                self._was_in_corner = False

        listener_kwargs: dict = {"on_press": on_press, "on_release": on_release}

        self._mouse_listener = mouse.Listener(on_move=on_move)
        self._key_listener   = keyboard.Listener(**listener_kwargs)

        self._mouse_listener.start()
        self._key_listener.start()
        self._mouse_listener.join()
        self._key_listener.join()
