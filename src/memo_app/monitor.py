from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal
from pynput import keyboard, mouse


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


class CornerMonitor(QThread):
    """
    각 디스플레이의 좌측 상단 코너에 마우스가 진입할 때 + Ctrl 키가 눌려 있으면
    신호를 발생시킨다.
    """

    corner_triggered = Signal()

    def __init__(self, corners: list[DisplayCorner] | None = None):
        super().__init__()
        self.corners: list[DisplayCorner] = corners if corners is not None else [DisplayCorner(0, 0, 20)]
        self._ctrl_pressed = False
        self._was_in_corner = False
        self._mouse_listener: mouse.Listener | None = None
        self._key_listener: keyboard.Listener | None = None

    @property
    def corner_size(self) -> int:
        return self.corners[0].corner_size if self.corners else 20

    @corner_size.setter
    def corner_size(self, v: int):
        for c in self.corners:
            c.corner_size = v

    def _in_any_corner(self, x: int, y: int) -> bool:
        return any(c.in_corner(x, y) for c in self.corners)

    def run(self):
        self._mouse_x = 0
        self._mouse_y = 0

        def on_move(x, y):
            self._mouse_x = x
            self._mouse_y = y
            in_corner = self._in_any_corner(x, y)
            if self._ctrl_pressed and in_corner and not self._was_in_corner:
                self.corner_triggered.emit()
            self._was_in_corner = in_corner

        def on_press(key):
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
                self._ctrl_pressed = True
                if self._in_any_corner(self._mouse_x, self._mouse_y):
                    self.corner_triggered.emit()

        def on_release(key):
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
                self._ctrl_pressed = False
                self._was_in_corner = False

        self._mouse_listener = mouse.Listener(on_move=on_move)
        self._key_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

        self._mouse_listener.start()
        self._key_listener.start()
        self._mouse_listener.join()
        self._key_listener.join()

    def stop_listeners(self):
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._key_listener:
            self._key_listener.stop()
