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

測試分成一般單元測試與 Linux/X11 整合測試。一般單元測試使用假後端驗證重置、間隔、方向與 log，不需要安裝額外套件；Linux/X11 整合測試由 Testcontainers 建立 Linux 容器，並以 Xvfb 提供虛擬 X11 桌面確認實際鼠標事件。

Windows 執行一般單元測試：

    py -3 -m unittest discover -s tests -p "test_*.py" -v

Linux/X11 整合測試需要 Docker Desktop 或其他可用的 Docker Engine，以及 Python 3.10 或更新版本。於工具目錄執行：

    py -3 -m pip install -r requirements-test.txt
    py -3 tests/run_testcontainers.py

`requirements-test.txt` 安裝主機端的 Testcontainers 執行器；`python-xlib` 僅由容器從 `requirements-integration.txt` 安裝。容器測試只驗證 Linux X11 路徑；Windows、macOS 與 Wayland 的原生桌面互動仍需在對應桌面工作階段驗證。

## 平台說明

- Windows 使用 SendInput 送出絕對鼠標移動事件。
- macOS 使用 Quartz 建立並送出鼠標移動事件。
- Linux X11 使用 XTEST extension。
- Linux Wayland 使用 XDG RemoteDesktop 與 ScreenCast portal，需選擇螢幕以取得該串流的邏輯座標；工具不讀取畫面影像。
