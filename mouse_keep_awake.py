from __future__ import annotations

import argparse
import logging
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Protocol

from mouse_backend import create_backend


INTERVAL_SECONDS = 5 * 60
MOVEMENTS = ((-5, -5), (5, -5), (-5, 5), (5, 5))
DIRECTION_NAMES = {
    (-5, -5): "左上",
    (5, -5): "右上",
    (-5, 5): "左下",
    (5, 5): "右下",
}


class MouseBackend(Protocol):
    name: str

    def move_to_origin(self) -> None: ...

    def move_relative(self, dx: int, dy: int) -> None: ...

    def close(self) -> None: ...


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def next_wall_time(interval_seconds: int) -> str:
    next_at = datetime.now().astimezone() + timedelta(seconds=interval_seconds)
    return next_at.replace(microsecond=0).isoformat()


def run(backend: MouseBackend, interval_seconds: int = INTERVAL_SECONDS) -> None:
    logger = logging.getLogger("mouse_keep_awake")
    logger.info("工具啟動，平台後端：%s", backend.name)

    backend.move_to_origin()
    logger.info("已送出鼠標移至 (0, 0) 的互動事件")
    logger.info("下次移動時間：%s", next_wall_time(interval_seconds))

    while True:
        time.sleep(interval_seconds)
        dx, dy = random.choice(MOVEMENTS)
        backend.move_relative(dx, dy)
        logger.info(
            "已送出鼠標移動事件：%s（dx=%d, dy=%d）",
            DIRECTION_NAMES[(dx, dy)],
            dx,
            dy,
        )
        logger.info("下次移動時間：%s", next_wall_time(interval_seconds))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="每五分鐘送出鼠標移動事件，讓系統持續收到互動訊號。"
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=INTERVAL_SECONDS,
        help="移動間隔秒數，預設為 300 秒。",
    )
    args = parser.parse_args()
    if args.interval_seconds < 1:
        parser.error("--interval-seconds 必須大於 0")

    configure_logging()
    logger = logging.getLogger("mouse_keep_awake")
    backend: MouseBackend | None = None
    try:
        logger.info("正在初始化平台鼠標事件後端")
        backend = create_backend()
        run(backend, args.interval_seconds)
    except KeyboardInterrupt:
        logger.info("收到停止指令，工具已停止")
    except Exception as error:
        logger.exception("工具停止：%s", error)
        return 1
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:
                logger.exception("關閉平台後端時發生錯誤")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())