#!/bin/bash
cd "$(dirname "$0")"
python3 mouse_keep_awake.py "$@"
status=$?
echo
read -r -p "按 Enter 關閉此視窗..." _
exit "$status"