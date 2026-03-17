@echo off
cd /d D:\agent_litkb
call agent\Scripts\activate.bat
echo Starting vLLM OpenAI-compatible server for DeepSeek-R1 on port 8000 ...
echo Using local model: D:\agent_litkb\r1_model

python -m vllm.entrypoints.openai.api_server ^
    --model D:\agent_litkb\r1_model ^
    --tensor-parallel-size 1 ^
    --gpu-memory-utilization 0.85 ^
    --port 8000 ^
    --max-model-len 4096 ^
    --trust-remote-code

pause
