@echo off
cd /d D:\agent_litkb
call agent\Scripts\activate.bat
echo Starting FastAPI backend on http://127.0.0.1:9000 ...
uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload

