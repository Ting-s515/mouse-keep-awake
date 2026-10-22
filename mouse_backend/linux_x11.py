import ctypes
import ctypes.util


class LinuxX11Backend:
    name = "Linux X11 XTEST"

    def __init__(self) -> None:
        x11_name = ctypes.util.find_library("X11")
        xtst_name = ctypes.util.find_library("Xtst")
        if not x11_name or not xtst_name:
            raise RuntimeError("找不到 X11/XTEST 系統函式庫")
        self._x11 = ctypes.CDLL(x11_name)
        self._xtst = ctypes.CDLL(xtst_name)

        self._x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self._x11.XOpenDisplay.restype = ctypes.c_void_p
        self._x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self._x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
        self._x11.XDefaultScreen.restype = ctypes.c_int
        self._x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        self._x11.XDefaultRootWindow.restype = ctypes.c_ulong
        self._x11.XQueryPointer.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint),
        ]
        self._x11.XQueryPointer.restype = ctypes.c_int
        self._x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._xtst.XTestFakeMotionEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        self._xtst.XTestFakeMotionEvent.restype = ctypes.c_int

        self._display = self._x11.XOpenDisplay(None)
        if not self._display:
            raise RuntimeError("無法連線到 X11 DISPLAY")
        self._screen = self._x11.XDefaultScreen(self._display)
        self._root = self._x11.XDefaultRootWindow(self._display)

    def move_to_origin(self) -> None:
        self._move_absolute(0, 0)

    def move_relative(self, dx: int, dy: int) -> None:
        root_return = ctypes.c_ulong()
        child_return = ctypes.c_ulong()
        root_x = ctypes.c_int()
        root_y = ctypes.c_int()
        window_x = ctypes.c_int()
        window_y = ctypes.c_int()
        mask = ctypes.c_uint()
        found = self._x11.XQueryPointer(
            self._display,
            self._root,
            ctypes.byref(root_return),
            ctypes.byref(child_return),
            ctypes.byref(root_x),
            ctypes.byref(root_y),
            ctypes.byref(window_x),
            ctypes.byref(window_y),
            ctypes.byref(mask),
        )
        if not found:
            raise RuntimeError("無法讀取 X11 游標位置")
        self._move_absolute(root_x.value + dx, root_y.value + dy)

    def _move_absolute(self, x: int, y: int) -> None:
        sent = self._xtst.XTestFakeMotionEvent(
            self._display,
            self._screen,
            x,
            y,
            0,
        )
        if not sent:
            raise RuntimeError("X11 XTEST 未接受鼠標移動事件")
        self._x11.XSync(self._display, 0)

    def close(self) -> None:
        if self._display:
            self._x11.XCloseDisplay(self._display)
            self._display = None