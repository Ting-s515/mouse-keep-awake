import ctypes
from ctypes import wintypes


INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", wintypes.DWORD), ("data", INPUT_UNION)]


class WindowsBackend:
    name = "Windows SendInput"

    def __init__(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        self._user32.GetCursorPos.restype = wintypes.BOOL
        self._user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        self._user32.GetSystemMetrics.restype = ctypes.c_int
        self._user32.SendInput.argtypes = [
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        ]
        self._user32.SendInput.restype = wintypes.UINT

    def move_to_origin(self) -> None:
        self._move_absolute(0, 0)

    def move_relative(self, dx: int, dy: int) -> None:
        point = POINT()
        if not self._user32.GetCursorPos(ctypes.byref(point)):
            raise ctypes.WinError(ctypes.get_last_error())
        self._move_absolute(point.x + dx, point.y + dy)

    def _move_absolute(self, x: int, y: int) -> None:
        left = self._user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = self._user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = self._user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = self._user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        if width < 2 or height < 2:
            raise RuntimeError("無法取得 Windows 虛擬螢幕尺寸")

        x = min(max(x, left), left + width - 1)
        y = min(max(y, top), top + height - 1)
        normalized_x = round((x - left) * 65535 / (width - 1))
        normalized_y = round((y - top) * 65535 / (height - 1))
        event = INPUT(
            type=INPUT_MOUSE,
            data=INPUT_UNION(
                mi=MOUSEINPUT(
                    dx=normalized_x,
                    dy=normalized_y,
                    mouseData=0,
                    dwFlags=MOUSEEVENTF_MOVE
                    | MOUSEEVENTF_ABSOLUTE
                    | MOUSEEVENTF_VIRTUALDESK,
                    time=0,
                    dwExtraInfo=0,
                )
            ),
        )
        sent = self._user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent != 1:
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        return None