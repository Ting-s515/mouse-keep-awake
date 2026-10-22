import asyncio
import threading
import uuid

from dbus_next import Variant
from dbus_next.aio import MessageBus


BUS_NAME = "org.freedesktop.portal.Desktop"
DESKTOP_PATH = "/org/freedesktop/portal/desktop"
REMOTE_DESKTOP = "org.freedesktop.portal.RemoteDesktop"
SCREEN_CAST = "org.freedesktop.portal.ScreenCast"
REQUEST = "org.freedesktop.portal.Request"
SESSION = "org.freedesktop.portal.Session"


def _token(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LinuxWaylandBackend:
    name = "Linux Wayland RemoteDesktop portal"

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._session_handle = None
        self._stream_id = None
        try:
            self._submit(self._open_session()).result(timeout=150)
        except Exception:
            self.close()
            raise

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self._loop)

    async def _open_session(self) -> None:
        self._bus = await MessageBus().connect()
        introspection = await self._bus.introspect(BUS_NAME, DESKTOP_PATH)
        desktop = self._bus.get_proxy_object(BUS_NAME, DESKTOP_PATH, introspection)
        self._remote = desktop.get_interface(REMOTE_DESKTOP)
        self._screen_cast = desktop.get_interface(SCREEN_CAST)

        session_results = await self._request(
            self._remote,
            "create_session",
            {
                "handle_token": Variant("s", _token("create")),
                "session_handle_token": Variant("s", _token("session")),
            },
        )
        self._session_handle = self._variant_value(session_results["session_handle"])

        await self._request(
            self._remote,
            "select_devices",
            self._session_handle,
            {
                "types": Variant("u", 2),
                "handle_token": Variant("s", _token("devices")),
            },
        )
        await self._request(
            self._screen_cast,
            "select_sources",
            self._session_handle,
            {
                "types": Variant("u", 1),
                "multiple": Variant("b", False),
                "handle_token": Variant("s", _token("sources")),
            },
        )
        start_results = await self._request(
            self._remote,
            "start",
            self._session_handle,
            "",
            {"handle_token": Variant("s", _token("start"))},
        )
        streams = self._variant_value(start_results.get("streams", []))
        if not streams:
            raise RuntimeError("Wayland portal 未提供螢幕座標串流")
        self._stream_id = streams[0][0]

    async def _request(self, interface, method: str, *args):
        request_path = await getattr(interface, f"call_{method}")(*args)
        introspection = await self._bus.introspect(BUS_NAME, request_path)
        request_object = self._bus.get_proxy_object(
            BUS_NAME,
            request_path,
            introspection,
        )
        request_interface = request_object.get_interface(REQUEST)
        response_future = self._loop.create_future()

        def receive_response(response, results):
            if not response_future.done():
                response_future.set_result((response, results))

        request_interface.on_response(receive_response)
        try:
            response, results = await asyncio.wait_for(response_future, timeout=120)
        finally:
            request_interface.off_response(receive_response)
        if response != 0:
            raise RuntimeError(f"Wayland portal 請求未獲授權，代碼：{response}")
        return results

    @staticmethod
    def _variant_value(value):
        return value.value if isinstance(value, Variant) else value

    def move_to_origin(self) -> None:
        self._submit(
            self._remote.call_notify_pointer_motion_absolute(
                self._session_handle,
                {},
                self._stream_id,
                0.0,
                0.0,
            )
        ).result(timeout=15)

    def move_relative(self, dx: int, dy: int) -> None:
        self._submit(
            self._remote.call_notify_pointer_motion(
                self._session_handle,
                {},
                float(dx),
                float(dy),
            )
        ).result(timeout=15)

    async def _close_session(self) -> None:
        if not getattr(self, "_bus", None):
            return
        if self._session_handle:
            try:
                introspection = await self._bus.introspect(
                    BUS_NAME,
                    self._session_handle,
                )
                session_object = self._bus.get_proxy_object(
                    BUS_NAME,
                    self._session_handle,
                    introspection,
                )
                session_interface = session_object.get_interface(SESSION)
                await session_interface.call_close()
            except Exception:
                pass
        self._bus.disconnect()

    def close(self) -> None:
        if self._loop.is_running():
            try:
                self._submit(self._close_session()).result(timeout=10)
            finally:
                self._loop.call_soon_threadsafe(self._loop.stop)
                self._thread.join(timeout=5)