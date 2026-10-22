# 鼠標互動小工具

獨立的 Python 命令列工具。啟動後立即將游標移至 (0, 0)，接著每五分鐘隨機選一個象限送出 5px 鼠標移動事件，讓作業系統持續收到鼠標互動。

## 執行

需要 Python 3.10 或更新版本。

- Windows：雙擊 run_windows.bat。
- macOS：先在終端機執行 chmod +x run_macos.command，之後可雙擊 run_macos.command。若系統要求控制輔助使用功能，需在「系統設定 > 隱私權與安全性 > 輔助使用」允許執行該工具的終端機或 Python。
- Linux X11：在終端機執行 sh run_linux.sh。
- Linux Wayland：先安裝依賴，再在終端機執行 sh run_linux.sh。

Linux Wayland 依賴安裝方式：

    python3 -m pip install -r requirements.txt

Wayland 會透過桌面 portal 要求鼠標控制及螢幕座標串流授權。授權流程由桌面環境顯示。若拒絕授權，工具會輸出錯誤並停止。

## 執行 log

終端機會顯示啟動平台、初始重置、每次移動方向和下次移動時間。按 Ctrl+C 停止。

可用 --interval-seconds 暫時調整移動間隔，例如：

    python3 mouse_keep_awake.py --interval-seconds 10

## 測試

測試分成兩部分：假後端單元測試驗證重置、間隔、方向與 log；Testcontainers 會建立 Linux 容器並以 Xvfb 提供虛擬 X11 桌面，確認 X11 後端實際送出鼠標移動事件。

需要 Docker Desktop 或其他可用的 Docker Engine，以及 Python 3.10 或更新版本。於工具目錄執行：

    python -m pip install -r requirements-test.txt
    python tests/run_testcontainers.py

容器測試只驗證 Linux X11 路徑；Windows、macOS 與 Wayland 的原生桌面互動仍需在對應桌面工作階段驗證。

## 平台說明

- Windows 使用 SendInput 送出絕對鼠標移動事件。
- macOS 使用 Quartz 建立並送出鼠標移動事件。
- Linux X11 使用 XTEST extension。
- Linux Wayland 使用 XDG RemoteDesktop 與 ScreenCast portal，需選擇螢幕以取得該串流的邏輯座標；工具不讀取畫面影像。
