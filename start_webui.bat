@echo off
cd /d D:\agent_litkb
call agent\Scripts\activate.bat
echo Starting Gradio Web UI on http://127.0.0.1:7860 ...
python -m webui.app

