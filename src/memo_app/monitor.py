from PySide6.QtCore import QThread, Signal
from pynput import keyboard, mouse


class CornerMonitor(QThread):
    """
    마우스가 화면 좌측 상단 코너에 진입할 때 + Ctrl 키가 눌려 있으면 신호를 발생시킨다.
    """

    corner_triggered = Signal()

    def __init__(self, corner_size: int = 20):
        super().__init__()
        self.corner_size = corner_size
        self._ctrl_pressed = False
        self._was_in_corner = False
        self._mouse_listener: mouse.Listener | None = None
        self._key_listener: keyboard.Listener | None = None

    def run(self):
        self._mouse_x = 0
        self._mouse_y = 0

        def on_move(x, y):
            self._mouse_x = x
            self._mouse_y = y
            in_corner = x <= self.corner_size and y <= self.corner_size
            if self._ctrl_pressed and in_corner and not self._was_in_corner:
                self.corner_triggered.emit()
            self._was_in_corner = in_corner

        def on_press(key):
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
                self._ctrl_pressed = True
                # 이미 코너에 있을 때 Ctrl을 누른 경우에도 트리거
                if self._mouse_x <= self.corner_size and self._mouse_y <= self.corner_size:
                    self.corner_triggered.emit()

        def on_release(key):
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.ctrl):
                self._ctrl_pressed = False
                self._was_in_corner = False  # 다음 진입 시 재트리거 허용

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
