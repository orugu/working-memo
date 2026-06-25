from __future__ import annotations

import platform
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal
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
      key_only   — 마우스 위치 무관, 퀵키만 입력 (macOS는 Quartz로 키 억제)
    """

    corner_triggered = Signal(int, int)  # (origin_x, origin_y) of the triggered display

    def __init__(
        self,
        corners: list[DisplayCorner] | None = None,
        quick_key: str = "ctrl",
        trigger_mode: str = "corner_key",
    ):
        super().__init__()
        self.corners: list[DisplayCorner] = corners if corners is not None else [DisplayCorner(0, 0, 20)]
        self.quick_key    = quick_key
        self.trigger_mode = trigger_mode
        self._key_pressed  = False
        self._was_in_corner = False
        self._mouse_x = 0
        self._mouse_y = 0
        self._mouse_listener: mouse.Listener | None = None
        self._key_listener:   keyboard.Listener | None = None

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

    def run(self):
        def on_move(x, y):
            self._mouse_x = x
            self._mouse_y = y
            if self.trigger_mode == "corner_key":
                in_corner = self._in_any_corner(x, y)
                if self._key_pressed and in_corner and not self._was_in_corner:
                    ox, oy = self._corner_origin(x, y)
                    self.corner_triggered.emit(ox, oy)
                self._was_in_corner = in_corner

        def on_press(key):
            if not self._matches(key):
                return
            self._key_pressed = True
            if self.trigger_mode == "key_only":
                ox, oy = self._corner_origin(self._mouse_x, self._mouse_y)
                self.corner_triggered.emit(ox, oy)
            elif self._in_any_corner(self._mouse_x, self._mouse_y):
                ox, oy = self._corner_origin(self._mouse_x, self._mouse_y)
                self.corner_triggered.emit(ox, oy)

        def on_release(key):
            if self._matches(key):
                self._key_pressed = False
                self._was_in_corner = False

        listener_kwargs: dict = {"on_press": on_press, "on_release": on_release}

        # macOS: key_only 모드에서 Quartz로 트리거 키를 다른 앱에 전달하지 않음
        if _HAS_QUARTZ and self.trigger_mode == "key_only":
            codes = _DARWIN_KEY_CODES.get(self.quick_key, set())
            if codes:
                def _darwin_intercept(event_type, event):
                    key_code = _Quartz.CGEventGetIntegerValueField(
                        event, _Quartz.kCGKeyboardEventKeycode
                    )
                    if key_code in codes:
                        return None  # 억제: 다른 앱에 전달 안 됨
                    return event
                listener_kwargs["darwin_intercept"] = _darwin_intercept

        self._mouse_listener = mouse.Listener(on_move=on_move)
        self._key_listener   = keyboard.Listener(**listener_kwargs)

        self._mouse_listener.start()
        self._key_listener.start()
        self._mouse_listener.join()
        self._key_listener.join()

    def stop_listeners(self):
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._key_listener:
            self._key_listener.stop()
