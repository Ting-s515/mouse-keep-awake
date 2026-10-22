import os
import platform


def create_backend():
    system = platform.system()
    if system == "Windows":
        from .windows import WindowsBackend

        return WindowsBackend()
    if system == "Darwin":
        from .macos import MacOSBackend

        return MacOSBackend()
    if system == "Linux":
        if os.environ.get("WAYLAND_DISPLAY"):
            from .linux_wayland import LinuxWaylandBackend

            return LinuxWaylandBackend()
        from .linux_x11 import LinuxX11Backend

        return LinuxX11Backend()
    raise RuntimeError(f"不支援的作業系統：{system}")