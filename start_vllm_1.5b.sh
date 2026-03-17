#!/bin/bash
source ~/vllm_env/bin/activate
cd /mnt/d/agent_litkb

echo "启动 DeepSeek-R1-1.5B 模型..."
echo "模型路径: /mnt/d/agent_litkb/15b_model"
echo "正在启动，请等待..."

python -m vllm.entrypoints.openai.api_server \
    --model /mnt/d/agent_litkb/15b_model \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.85 \
    --port 8000 \
    --max-model-len 4096 \
    --trust-remote-code \
    --host 0.0.0.0
