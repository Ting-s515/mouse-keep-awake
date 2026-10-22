import ctypes


class CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


CG_EVENT_MOUSE_MOVED = 5
CG_HID_EVENT_TAP = 0
CG_MOUSE_BUTTON_LEFT = 0


class MacOSBackend:
    name = "macOS Quartz"

    def __init__(self) -> None:
        self._core_graphics = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        self._core_foundation = ctypes.CDLL(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        self._core_graphics.CGEventCreate.argtypes = [ctypes.c_void_p]
        self._core_graphics.CGEventCreate.restype = ctypes.c_void_p
        self._core_graphics.CGEventGetLocation.argtypes = [ctypes.c_void_p]
        self._core_graphics.CGEventGetLocation.restype = CGPoint
        self._core_graphics.CGEventCreateMouseEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            CGPoint,
            ctypes.c_uint32,
        ]
        self._core_graphics.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        self._core_graphics.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        self._core_foundation.CFRelease.argtypes = [ctypes.c_void_p]

    def move_to_origin(self) -> None:
        self._post_mouse_move(CGPoint(0.0, 0.0))

    def move_relative(self, dx: int, dy: int) -> None:
        current = self._core_graphics.CGEventCreate(None)
        if not current:
            raise RuntimeError("無法讀取 macOS 游標位置")
        try:
            point = self._core_graphics.CGEventGetLocation(current)
        finally:
            self._core_foundation.CFRelease(current)
        self._post_mouse_move(CGPoint(point.x + dx, point.y + dy))

    def _post_mouse_move(self, point: CGPoint) -> None:
        event = self._core_graphics.CGEventCreateMouseEvent(
            None,
            CG_EVENT_MOUSE_MOVED,
            point,
            CG_MOUSE_BUTTON_LEFT,
        )
        if not event:
            raise RuntimeError("無法建立 macOS 鼠標移動事件")
        try:
            self._core_graphics.CGEventPost(CG_HID_EVENT_TAP, event)
        finally:
            self._core_foundation.CFRelease(event)

    def close(self) -> None:
        return None